import {defineStore} from "pinia";
import {AppInfoDTO, LicenseDTO} from "@/generated-sources";
import {IUserProfileMinimal} from "@/interfaces";
import mixpanel from "mixpanel-browser";
import {anonymize} from "@/utils";
// import Vue from "vue";
import {api} from "@/api";
import {AxiosError} from "axios";
import {useUserStore} from "@/stores/user";
import {TYPE, useToast} from "vue-toastification";

export interface AppNotification {
    content: string;
    color?: TYPE
    showProgress?: boolean;
}

const toast = useToast();

interface State {
    appSettings: AppInfoDTO | null;
    license: LicenseDTO | null;
    coworkers: IUserProfileMinimal[];
    notifications: AppNotification[];
    backendReady: boolean;
}

export const useMainStore = defineStore('main', {
    state: (): State => ({
        appSettings: null,
        license: null,
        coworkers: [],
        notifications: [],
        backendReady: true
    }),
    getters: {
        authAvailable(state: State) {
            return state.license?.features.AUTH;
        }
    },
    actions: {
        roleName(value: string) {
            if (this.appSettings) {
                const roles = Object.assign({}, ...this.appSettings.roles.map((x) => ({[x.id]: x.name})));
                if (value in roles) {
                    return roles[value];
                } else {
                    return value;
                }
            }
        },
        setAppSettings(payload: AppInfoDTO) {
            const userStore = useUserStore();
            this.appSettings = payload;
            if (this.appSettings.generalSettings.isAnalyticsEnabled && !mixpanel.has_opted_in_tracking()) {
                mixpanel.opt_in_tracking();
            } else if (!this.appSettings.generalSettings.isAnalyticsEnabled && !mixpanel.has_opted_out_tracking()) {
                mixpanel.opt_out_tracking();
            }
            const instanceId = this.appSettings.generalSettings.instanceId;
            if (userStore.userProfile) {
                mixpanel.alias(`${instanceId}-${anonymize(userStore.userProfile?.user_id)}`);
            }
            mixpanel.people.set(
                {
                    "Giskard Instance": instanceId,
                    "Giskard Version": this.appSettings.version,
                    "Giskard Plan": this.appSettings.planCode,
                    "Giskard LicenseID": this.license?.licenseId ?? "NONE",
                    "Is HuggingFace": this.appSettings?.isRunningOnHfSpaces,
                    "HuggingFace Space ID": this.appSettings?.hfSpaceId,
                }
            );
            mixpanel.track("Read App Settings")
        },
        addSimpleNotification(text: string) {
            this.addNotification({content: text, color: TYPE.SUCCESS})
        },
        addNotification(payload: AppNotification) {
            toast(payload.content, {
                closeButton: false,
                icon: payload.showProgress ? 'notification-spinner fas fa-spinner fa-spin' : true,
                type: payload.color
            });
        },
        removeNotification(payload: AppNotification) {
            toast.clear();
        },
        async fetchAppSettings() {
            const response = await api.getUserAndAppSettings();
            this.setAppSettings(response.app);
        },
        async fetchLicense() {
            try {
                this.license = await api.getLicense();
                this.backendReady = true;
            } catch (e) {
                this.backendReady = false
                throw e;
            }
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
            } catch (error: any) {
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

