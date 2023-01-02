import {defineStore} from "pinia";
import {AdminUserDTO, AppConfigDTO, ProjectDTO, UpdateMeDTO} from "@/generated-sources";
import {IUserProfileMinimal} from "@/interfaces";
import AppInfoDTO = AppConfigDTO.AppInfoDTO;
import mixpanel from "mixpanel-browser";
import {anonymize, getLocalToken, removeLocalToken, saveLocalToken} from "@/utils";
import Vue, {ref} from "vue";
import {api} from "@/api";
import {AxiosError} from "axios";
import {useUserStore} from "@/stores/user";

export interface AppNotification {
    content: string;
    color?: string;
    showProgress?: boolean;
}

interface State {
    appSettings: AppInfoDTO | null;
    coworkers: IUserProfileMinimal[];
    notifications: AppNotification[];
}

export const useMainStore = defineStore('main', {
    state: (): State => ({
        appSettings: null,
        coworkers: [],
        notifications: [],
    }),
    getters: {
    },
    actions: {
        setAppSettings(payload: AppInfoDTO) {
            const userStore = useUserStore();
            this.appSettings = payload;
            if (this.appSettings.generalSettings.isAnalyticsEnabled && !mixpanel.has_opted_in_tracking()) {
                mixpanel.opt_in_tracking();
            } else if (!this.appSettings.generalSettings.isAnalyticsEnabled && !mixpanel.has_opted_out_tracking()) {
                mixpanel.opt_out_tracking();
            }
            let instanceId = this.appSettings.generalSettings.instanceId;
            if (userStore.userProfile) {
                mixpanel.alias(`${instanceId}-${anonymize(userStore.userProfile?.user_id)}`);
            }
            mixpanel.people.set(
                {
                    "Giskard Instance": instanceId,
                    "Giskard Version": this.appSettings.version,
                    "Giskard Plan": this.appSettings.planCode
                }
            );
            mixpanel.track("Read App Settings")
            const self = this;
            Vue.filter('roleName', function (value) {
                if (self.appSettings) {
                    let roles = Object.assign({}, ...self.appSettings.roles.map((x) => ({[x.id]: x.name})));
                    if (value in roles) {
                        return roles[value];
                    } else {
                        return value;
                    }
                }
            });
        },
        addNotification(payload: AppNotification) {
            Vue.$toast(payload.content, {
                closeButton: false,
                icon: payload.showProgress ? 'notification-spinner fas fa-spinner fa-spin' : true
            });
        },
        removeNotification(payload: AppNotification) {
            Vue.$toast.clear();
        },
        async getUserProfile() {
            const userStore = useUserStore();
            const response = await api.getUserAndAppSettings();
            if (response) {
                userStore.userProfile = response.user;
                this.appSettings = response.app;
            }
        },
        async getCoworkers() {
            try {
                const response = await api.getCoworkersMinimal();
                if (response) {
                    this.coworkers = response;
                }
            } catch (error) {
                await this.checkApiError(error);
            }
        },
        async checkApiError(payload: AxiosError) {
            const userStore = useUserStore();
            if (payload.response!.status === 401) {
                await userStore.logout();
            }
        }
    }
})