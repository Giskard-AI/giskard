import {defineStore} from "pinia";
import {AdminUserDTO, AppConfigDTO, ProjectDTO, UpdateMeDTO} from "@/generated-sources";
import {IUserProfileMinimal} from "@/interfaces";
import {AppNotification, MainState} from "@/store/main/state";
import AppInfoDTO = AppConfigDTO.AppInfoDTO;
import {Role} from "@/enums";
import mixpanel from "mixpanel-browser";
import {anonymize, getLocalToken, removeLocalToken, saveLocalToken} from "@/utils";
import Vue from "vue";
import {api} from "@/api";
import {
    commitAddNotification, commitRemoveNotification, commitSetAppSettings,
    commitSetCoworkers,
    commitSetLoggedIn,
    commitSetLogInError,
    commitSetToken, commitSetUserProfile
} from "@/store/main/mutations";
import {
    dispatchCheckApiError,
    dispatchGetUserProfile,
    dispatchLogOut, dispatchRemoveLogIn,
    dispatchRouteLoggedIn
} from "@/store/main/actions";
import router from "@/router";
import {AxiosError} from "axios";

interface State {
    token: string;
    isLoggedIn: boolean | null;
    logInError: string | null;
    userProfile: AdminUserDTO | null;
    appSettings: AppInfoDTO | null;
    coworkers: IUserProfileMinimal[];
    notifications: AppNotification[];
    projects: ProjectDTO[];
}

export const useMainStore = defineStore('main', {
    state: (): State => ({
        isLoggedIn: null,
        token: '',
        logInError: null,
        userProfile: null,
        appSettings: null,
        coworkers: [],
        notifications: [],
        projects: [],
    }),
    getters: {
        hasAdminAccess: (state: State) => {
            return (
                state.userProfile &&
                state.userProfile.roles?.includes(Role.ADMIN) &&
                state.userProfile.enabled);
        },
        loginError: (state: State) => state.logInError,
        allProjects: (state: State) => state.projects,
        project: (state: State) => (id: number) => {
            const filtered = state.projects.filter((p) => p.id === id);
            if (filtered.length > 0) return filtered[0];
            else return undefined;
        },
    },
    actions: {
        setAppSettings(payload: AppInfoDTO) {
            this.appSettings = payload;
            if (this.appSettings.generalSettings.isAnalyticsEnabled && !mixpanel.has_opted_in_tracking()) {
                mixpanel.opt_in_tracking();
            } else if (!this.appSettings.generalSettings.isAnalyticsEnabled && !mixpanel.has_opted_out_tracking()) {
                mixpanel.opt_out_tracking();
            }
            let instanceId = this.appSettings.generalSettings.instanceId;
            if (this.userProfile) {
                mixpanel.alias(`${instanceId}-${anonymize(this.userProfile?.user_id)}`);
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
        setProject(payload: ProjectDTO) {
            const projects = this.projects.filter((p: ProjectDTO) => p.id !== payload.id);
            projects.push(payload);
            this.projects = projects;
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
        async login(payload: { username: string; password: string }) {
            try {
                const response = await api.logInGetToken(payload.username, payload.password);
                const token = response.id_token;
                if (token) {
                    saveLocalToken(token);
                    this.token = token;
                    this.isLoggedIn = true;
                    this.logInError = null;
                    await this.getUserProfile();
                    await this.routeLoggedIn();
                    this.addNotification({content: 'Logged in', color: 'success'})
                } else {
                    await this.logout();
                }
            } catch (err) {
                this.logInError = err.response.data.detail;
                await this.logout();
            }
        },
        async getUserProfile() {
            const response = await api.getUserAndAppSettings();
            if (response) {
                this.userProfile = response.user;
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
        async updateUserProfile(payload: UpdateMeDTO) {
            const loadingNotification = {content: 'saving', showProgress: true};
            try {
                this.addNotification(loadingNotification);
                this.userProfile = await api.updateMe(payload);
                this.removeNotification(loadingNotification);
                this.addNotification({content: 'Profile successfully updated', color: 'success'});
            } catch (error) {
                await this.checkApiError(error);
                throw new Error(error.response.data.detail);
            }
        },
        async checkLoggedIn() {
            if (!this.isLoggedIn) {
                let token = this.token;
                if (!token) {
                    const localToken = getLocalToken();
                    if (localToken) {
                        this.token = localToken;
                        token = localToken;
                    }
                }
                if (token) {
                    const response = await api.getUserAndAppSettings();
                    this.isLoggedIn = true;
                    this.userProfile = response.user;
                    let appConfig = response.app;
                    this.setAppSettings(appConfig);
                } else {
                    this.removeLogin();
                }
            }
        },
        removeLogin() {
          removeLocalToken();
          this.token = '';
          this.isLoggedIn = false;
        },
        async logout() {
            this.removeLogin();
            await this.routeLogout();
        },
        async userLogout() {
          await this.logout();
          this.addNotification({content: 'Logged out', color: 'success'});
        },
        async routeLogout() {
            if (router.currentRoute.path !== '/auth/login') {
                await router.push('/auth/login');
            }
        },
        async checkApiError(payload: AxiosError) {
            if (payload.response!.status === 401) {
                await this.logout();
            }
        },
        async routeLoggedIn() {
            if (router.currentRoute.path === '/auth/login' || router.currentRoute.path === '/') {
                await router.push('/main');
            }
        }
    }
})