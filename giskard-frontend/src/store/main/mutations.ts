import {IUserProfileMinimal} from '@/interfaces';
import {AppNotification, MainState} from './state';
import {getStoreAccessors} from 'typesafe-vuex';
import {State} from '../state';
import {AdminUserDTO, AppConfigDTO, ProjectDTO} from '@/generated-sources';
import Vue from "vue";
import mixpanel from "mixpanel-browser";
import AppInfoDTO = AppConfigDTO.AppInfoDTO;
import {anonymize} from "@/utils";


export const mutations = {
    setToken(state: MainState, payload: string) {
        state.token = payload;
    },
    setLoggedIn(state: MainState, payload: boolean) {
        state.isLoggedIn = payload;
    },
    setLogInError(state: MainState, payload: string | null) {
        state.logInError = payload;
    },
    setUserProfile(state: MainState, payload: AdminUserDTO) {
        state.userProfile = payload;
    },
    setAppSettings(state: MainState, payload: AppInfoDTO) {
        state.appSettings = payload;
        if (state.appSettings.generalSettings.isAnalyticsEnabled && !mixpanel.has_opted_in_tracking()) {
            mixpanel.opt_in_tracking();
        } else if (!state.appSettings.generalSettings.isAnalyticsEnabled && !mixpanel.has_opted_out_tracking()) {
            mixpanel.opt_out_tracking();
        }
        let instanceId = state.appSettings.generalSettings.instanceId;
        if (state.userProfile) {
            mixpanel.alias(`${instanceId}-${anonymize(state.userProfile?.user_id)}`);
        }
        mixpanel.people.set(
            {
                "Giskard Instance": instanceId,
                "Giskard Version": state.appSettings.version,
                "Giskard Plan": state.appSettings.planCode
            }
        );
        mixpanel.track("Read App Settings")
        Vue.filter('roleName', function (value) {
            if (state.appSettings) {
                let roles = Object.assign({}, ...state.appSettings.roles.map((x) => ({[x.id]: x.name})));
                if (value in roles) {
                    return roles[value];
                } else {
                    return value;
                }
            }
        });
    },
    setCoworkers(state: MainState, payload: IUserProfileMinimal[]) {
        state.coworkers = payload;
    },
    setProjects(state: MainState, payload: ProjectDTO[]) {
        state.projects = payload;
    },
    setProject(state: MainState, payload: ProjectDTO) {
        const projects = state.projects.filter((p: ProjectDTO) => p.id !== payload.id);
        projects.push(payload);
        state.projects = projects;
    },
    addNotification(state: MainState, payload: AppNotification) {
        Vue.$toast(payload.content, {
            closeButton: false,
            icon: payload.showProgress ? 'notification-spinner fas fa-spinner fa-spin' : true
        });
    },
    removeNotification(state: MainState, payload: AppNotification) {
        Vue.$toast.clear();
    },
};

const {commit} = getStoreAccessors<MainState | any, State>('');

export const commitSetLoggedIn = commit(mutations.setLoggedIn);
export const commitSetLogInError = commit(mutations.setLogInError);
export const commitSetToken = commit(mutations.setToken);
export const commitSetUserProfile = commit(mutations.setUserProfile);
export const commitSetAppSettings = commit(mutations.setAppSettings);
export const commitSetCoworkers = commit(mutations.setCoworkers);
export const commitSetProjects = commit(mutations.setProjects);
export const commitSetProject = commit(mutations.setProject);
export const commitAddNotification = commit(mutations.addNotification);
export const commitRemoveNotification = commit(mutations.removeNotification);
