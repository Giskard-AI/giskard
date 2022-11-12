import {MainState} from './state';
import {getStoreAccessors} from 'typesafe-vuex';
import {State} from '../state';
import {Role} from '@/enums';

export const getters = {
    hasAdminAccess: (state: MainState) => {
        return (
            state.userProfile &&
            state.userProfile.roles?.includes(Role.ADMIN) &&
            state.userProfile.enabled);
    },
    loginError: (state: MainState) => state.logInError,
    userProfile: (state: MainState) => state.userProfile,
    appSettings: (state: MainState) => state.appSettings,
    token: (state: MainState) => state.token,
    isLoggedIn: (state: MainState) => state.isLoggedIn,
    firstNotification: (state: MainState) => state.notifications.length > 0 && state.notifications[0],
    coworkers: (state: MainState) => state.coworkers,
    allProjects: (state: MainState) => state.projects,
    project: (state: MainState) => (id: number) => {
        const filtered = state.projects.filter((p) => p.id === id);
        if (filtered.length > 0) return filtered[0];
        else return undefined;
    },
};

const {read} = getStoreAccessors<MainState, State>('');

export const readHasAdminAccess = read(getters.hasAdminAccess);
export const readUserProfile = read(getters.userProfile);
export const readAppSettings = read(getters.appSettings);
export const readCoworkers = read(getters.coworkers);
export const readFirstNotification = read(getters.firstNotification);
export const readAllProjects = read(getters.allProjects);
export const readProject = read(getters.project);
