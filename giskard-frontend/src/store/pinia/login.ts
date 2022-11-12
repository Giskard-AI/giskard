import {defineStore} from "pinia";
import Vue, {ref} from "vue";
import {api} from "@/api";
import router from "@/router";
import mixpanel from "mixpanel-browser";
import {anonymize, getLocalToken} from "@/utils";
import {AppConfigDTO} from "@/generated-sources";
import {AppNotification} from "@/store/notification";

export const useLoginStore = defineStore('login', () => {
    const loginError = ref();
    const token = ref();
    const isLoggedIn = ref();
    const logInError = ref();
    const userProfile = ref();
    const appSettings = ref();

    function setAppSettings(app: AppConfigDTO.AppInfoDTO) {
        appSettings.value = app;
        if (app.generalSettings.isAnalyticsEnabled && !mixpanel.has_opted_in_tracking()) {
            mixpanel.opt_in_tracking();
        } else if (!app.generalSettings.isAnalyticsEnabled && !mixpanel.has_opted_out_tracking()) {
            mixpanel.opt_out_tracking();
        }
        let instanceId = app.generalSettings.instanceId;
        if (userProfile.value) {
            mixpanel.alias(`${instanceId}-${anonymize(userProfile.value?.user_id)}`);
        }
        mixpanel.people.set(
            {
                "Giskard Instance": instanceId,
                "Giskard Version": app.version,
                "Giskard Plan": app.planCode
            }
        );
        mixpanel.track("Read App Settings")
        Vue.filter('roleName', function (value) {
            if (app) {
                let roles = Object.assign({}, ...app.roles.map((x) => ({[x.id]: x.name})));
                if (value in roles) {
                    return roles[value];
                } else {
                    return value;
                }
            }
        });
    }

    async function getUserProfile() {
        const response = await api.getUserAndAppSettings();
        if (response) {
            userProfile.value = response.user;
            setAppSettings(response.app);
        }
    }

    async function routeLoggedIn() {
        if (router.currentRoute.path === '/auth/login' || router.currentRoute.path === '/') {
            await router.push('/main');
        }
    }

    function addNotification(payload: AppNotification) {
        Vue.$toast(payload.content, {
            closeButton: false,
            icon: payload.showProgress ? 'notification-spinner fas fa-spinner fa-spin' : true
        });
    }

    function logOut() {
        localStorage.removeItem('token');
        token.value = '';
        isLoggedIn.value = false;
    }

    async function logIn(payload: { username: string; password: string }) {
        try {
            const response = await api.logInGetToken(payload.username, payload.password);
            if (response.id_token) {
                localStorage.setItem('token', response.id_token);
                token.value = response.id_token;
                isLoggedIn.value = true;
                logInError.value = null;

                await getUserProfile();
                await routeLoggedIn();

                addNotification({content: 'Logged in', color: 'success'});
            } else {
                logOut();
            }
        } catch (err) {
            loginError.value = err.response.data.detail;
            logOut();
        }
    }

    async function checkLoggedIn() {
        if (!isLoggedIn.value) {
            let t = token.value;
            if (!t) {
                const localToken = getLocalToken();
                if (localToken) {
                    token.value = localToken;
                    t = localToken;
                }
            }
            if (t) {
                const response = await api.getUserAndAppSettings();
                isLoggedIn.value = true;
                userProfile.value = response.user;
                setAppSettings(response.app);
            } else {
                logOut();
            }
        }
    }

    return {
        loginError,
        token,
        isLoggedIn,
        logInError,
        userProfile,
        appSettings,
        addNotification,
        checkLoggedIn,
        logIn
    }
})