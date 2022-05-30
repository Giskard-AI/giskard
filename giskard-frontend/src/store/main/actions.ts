import { api } from '@/api';
import router from '@/router';
import { getLocalToken, removeLocalToken, saveLocalToken } from '@/utils';
import { AxiosError } from 'axios';
import { getStoreAccessors } from 'typesafe-vuex';
import { ActionContext } from 'vuex';
import { State } from '../state';
import {
    commitAddNotification,
    commitRemoveNotification,
    commitSetLoggedIn,
    commitSetLogInError,
    commitSetToken,
    commitSetUserProfile,
    commitSetProjects,
    commitSetCoworkers,
    commitSetProject, commitSetAppSettings
} from './mutations';
import { AppNotification, MainState } from './state';
import { AdminUserDTO, ManagedUserVM, ProjectPostDTO, UpdateMeDTO } from '@/generated-sources';
import AdminUserDTOWithPassword = AdminUserDTO.AdminUserDTOWithPassword;

type MainContext = ActionContext<MainState, State>;

export const actions = {
    // Username here can be either User ID or email
    async actionLogIn(context: MainContext, payload: { username: string; password: string }) {
        try {
            const response = await api.logInGetToken(payload.username, payload.password);
            const token = response.id_token;
            if (token) {
                saveLocalToken(token);
                commitSetToken(context, token);
                commitSetLoggedIn(context, true);
                commitSetLogInError(context, null);
                await dispatchGetUserProfile(context);
                await dispatchRouteLoggedIn(context);
                commitAddNotification(context, { content: 'Logged in', color: 'success' });
            } else {
                await dispatchLogOut(context);
            }
        } catch (err) {
            commitSetLogInError(context, err.response.data.detail);
            await dispatchLogOut(context);
        }
    },
    async actionGetUserProfile(context: MainContext) {
        try {
            const response = await api.getMe();
            if (response) {
                commitSetUserProfile(context, response.user);
                commitSetAppSettings(context, response.app);
            }
        } catch (error) {
            await dispatchCheckApiError(context, error);
        }
    },
    async actionGetCoworkers(context: MainContext) {
        try {
            const response = await api.getCoworkersMinimal();
            if (response) {
                commitSetCoworkers(context, response);
            }
        } catch (error) {
            await dispatchCheckApiError(context, error);
        }
    },
    async actionUpdateUserProfile(context: MainContext, payload: UpdateMeDTO) {
        const loadingNotification = { content: 'saving', showProgress: true };
        try {
            commitAddNotification(context, loadingNotification);
            commitSetUserProfile(context, await api.updateMe( payload));
            commitRemoveNotification(context, loadingNotification);
            commitAddNotification(context, { content: 'Profile successfully updated', color: 'success' });
        } catch (error) {
            await dispatchCheckApiError(context, error);
            throw new Error(error.response.data.detail);
        }
    },
    async actionCheckLoggedIn(context: MainContext) {
        if (!context.state.isLoggedIn) {
            let token = context.state.token;
            if (!token) {
                const localToken = getLocalToken();
                if (localToken) {
                    commitSetToken(context, localToken);
                    token = localToken;
                }
            }
            if (token) {
                try {
                    const response = await api.getMe();
                    commitSetLoggedIn(context, true);
                    commitSetUserProfile(context, response.user);
                    commitSetAppSettings(context, response.app);
                } catch (error) {
                    await dispatchRemoveLogIn(context);
                }
            } else {
                await dispatchRemoveLogIn(context);
            }
        }
    },
    async actionRemoveLogIn(context: MainContext) {
        removeLocalToken();
        commitSetToken(context, '');
        commitSetLoggedIn(context, false);
    },
    async actionLogOut(context: MainContext) {
        await dispatchRemoveLogIn(context);
        await dispatchRouteLogOut(context);
    },
    async actionUserLogOut(context: MainContext) {
        await dispatchLogOut(context);
        commitAddNotification(context, { content: 'Logged out', color: 'success' });
    },
    actionRouteLogOut(context: MainContext) {
        if (router.currentRoute.path !== '/auth/login') {
            router.push('/auth/login');
        }
    },
    async actionCheckApiError(context: MainContext, payload: AxiosError) {
        if (payload.response!.status === 401) {
            await dispatchLogOut(context);
        }
    },
    actionRouteLoggedIn(context: MainContext) {
        if (router.currentRoute.path === '/auth/login' || router.currentRoute.path === '/') {
            router.push('/main');
        }
    },
    async removeNotification(context: MainContext, payload: { notification: AppNotification, timeout: number }) {
        return new Promise((resolve, reject) => {
            setTimeout(() => {
                commitRemoveNotification(context, payload.notification);
                resolve(true);
            }, payload.timeout);
        });
    },
    async passwordRecovery(context: MainContext, payload: { userId: string }) {
        const loadingNotification = { content: 'Sending password recovery email', showProgress: true };
        try {
            commitAddNotification(context, loadingNotification);
            await api.passwordRecovery(payload.userId);
            commitRemoveNotification(context, loadingNotification);
            commitAddNotification(context, { color: 'success', content: 'Password recovery link has been sent' });
            await dispatchLogOut(context);
        } catch (error) {
            commitRemoveNotification(context, loadingNotification);
            let data = error.response.data;
            let errMessage = "";
            if (data.message === 'error.validation') {
                errMessage = data.fieldErrors.map(e => `${e.field}: ${e.message}`).join('\n');
            } else {
                errMessage = data.detail;
            }
            commitAddNotification(context, { color: 'error', content: errMessage });
        }
    },
    async resetPassword(context: MainContext, payload: { password: string, token: string }) {
        const loadingNotification = { content: 'Resetting password', showProgress: true };
        try {
            commitAddNotification(context, loadingNotification);
            const response = await api.resetPassword(payload.password);
            commitRemoveNotification(context, loadingNotification);
            commitAddNotification(context, { color: 'success', content: 'Password successfully changed' });
            await dispatchLogOut(context);
        } catch (error) {
            commitAddNotification(context, { color: 'error', content: error.response.data.detail });
        }
    },
    async actionSignupUser(context: MainContext, payload: {userData: ManagedUserVM}) {
        const loadingNotification = { content: 'saving', showProgress: true };
        try {
            commitAddNotification(context, loadingNotification);
            await api.signupUser(payload.userData);
            commitRemoveNotification(context, loadingNotification);
            commitAddNotification(context, { content: 'Success! Please proceed to login', color: 'success' });
            await dispatchLogOut(context);
        } catch (error) {
            throw new Error(error.response.data.detail);
        }
    },
    async actionGetProjects(context: MainContext) {
        const loadingNotification = { content: 'Loading projects', showProgress: true };
        try {
            commitAddNotification(context, loadingNotification);
            const response = await api.getProjects();
            commitSetProjects(context, response)

            commitRemoveNotification(context, loadingNotification);
        } catch (error) {
            await dispatchCheckApiError(context, error);
        }
    },
    async actionGetProject(context: MainContext, payload: {id: number}) {
        const loadingNotification = { content: 'Loading project', showProgress: true };
        try {
            commitAddNotification(context, loadingNotification);
            const response = await api.getProject(payload.id);
            commitSetProject(context, response);
            commitRemoveNotification(context, loadingNotification);
        } catch (error) {
            await dispatchCheckApiError(context, error);
        }
    },
    async actionCreateProject(context: MainContext, payload: ProjectPostDTO) {
        const loadingNotification = { content: 'Saving...', showProgress: true };
        try {
            commitAddNotification(context, loadingNotification);
            await api.createProject( payload);
            commitRemoveNotification(context, loadingNotification);
            commitAddNotification(context, { content: 'Success' , color: 'success' });
            dispatchGetProjects(context);
        } catch (error) {
            await dispatchCheckApiError(context, error);
            throw new Error(error.response.data.detail);
        }
    },
    async actionDeleteProject(context: MainContext, payload: {id: number}) {
        const loadingNotification = { content: 'Deleting...', showProgress: true };
        try {
            commitAddNotification(context, loadingNotification);
            await api.deleteProject( payload.id);
            commitRemoveNotification(context, loadingNotification);
            commitAddNotification(context, { content: 'Success' , color: 'success' });
        } catch (error) {
            await dispatchCheckApiError(context, error);
        }
    },
    async actionEditProject(context: MainContext, payload: {id: number, data: ProjectPostDTO}) {
        const loadingNotification = { content: 'Deleting...', showProgress: true };
        try {
            commitAddNotification(context, loadingNotification);
            const response = await api.editProject( payload.id, payload.data);
            commitRemoveNotification(context, loadingNotification);
            commitAddNotification(context, { content: 'Success' , color: 'success' });
            commitSetProject(context, response);
        } catch (error) {
            commitRemoveNotification(context, loadingNotification);

            await dispatchCheckApiError(context, error);
        }
    },
    async actionInviteUserToProject(context: MainContext, payload: {projectId: number, userId: number}) {
        const loadingNotification = { content: 'Sending...', showProgress: true };
        try {
            commitAddNotification(context, loadingNotification);
            const response = await api.inviteUserToProject( payload.projectId, payload.userId);
            commitRemoveNotification(context, loadingNotification);
            commitAddNotification(context, { content: 'Done' , color: 'success' });
            commitSetProject(context, response);
        } catch (error) {
            await dispatchCheckApiError(context, error);
            throw new Error(error.response.data.detail);
        }
    },
    async actionUninviteUserFromProject(context: MainContext, payload: {projectId: number, userId: number}) {
		const loadingNotification = { content: 'Sending...', showProgress: true };
        try {
			commitAddNotification(context, loadingNotification);
            const response = await api.uninviteUserFromProject( payload.projectId, payload.userId);
            commitSetProject(context, response);
			commitRemoveNotification(context, loadingNotification);
            commitAddNotification(context, { content: 'Done' , color: 'success' });
        } catch (error) {
			commitRemoveNotification(context, loadingNotification);

            await dispatchCheckApiError(context, error);
            throw new Error(error.response.data.detail);
        }
    },
};

const { dispatch } = getStoreAccessors<MainState | any, State>('');

export const dispatchCheckApiError = dispatch(actions.actionCheckApiError);
export const dispatchCheckLoggedIn = dispatch(actions.actionCheckLoggedIn);
export const dispatchGetUserProfile = dispatch(actions.actionGetUserProfile);
export const dispatchGetCoworkers = dispatch(actions.actionGetCoworkers);
export const dispatchLogIn = dispatch(actions.actionLogIn);
export const dispatchLogOut = dispatch(actions.actionLogOut);
export const dispatchUserLogOut = dispatch(actions.actionUserLogOut);
export const dispatchRemoveLogIn = dispatch(actions.actionRemoveLogIn);
export const dispatchRouteLoggedIn = dispatch(actions.actionRouteLoggedIn);
export const dispatchRouteLogOut = dispatch(actions.actionRouteLogOut);
export const dispatchUpdateUserProfile = dispatch(actions.actionUpdateUserProfile);
export const dispatchRemoveNotification = dispatch(actions.removeNotification);
export const dispatchPasswordRecovery = dispatch(actions.passwordRecovery);
export const dispatchResetPassword = dispatch(actions.resetPassword);
export const dispatchSignupUser = dispatch(actions.actionSignupUser);
export const dispatchGetProjects = dispatch(actions.actionGetProjects);
export const dispatchGetProject = dispatch(actions.actionGetProject);
export const dispatchCreateProject = dispatch(actions.actionCreateProject);
export const dispatchDeleteProject = dispatch(actions.actionDeleteProject);
export const dispatchEditProject = dispatch(actions.actionEditProject);
export const dispatchInviteUserToProject = dispatch(actions.actionInviteUserToProject);
export const dispatchUninviteUser = dispatch(actions.actionUninviteUserFromProject);
