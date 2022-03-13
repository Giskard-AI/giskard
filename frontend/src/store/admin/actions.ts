import { api } from '@/api';
import { ActionContext } from 'vuex';
import {IUserProfile, IUserProfileCreate, IUserProfileUpdate} from '@/interfaces';
import { State } from '../state';
import { AdminState } from './state';
import { getStoreAccessors } from 'typesafe-vuex';
import { commitSetUsers, commitSetUser, mutations, commitSetRoles } from './mutations';
import { dispatchCheckApiError } from '../main/actions';
import { commitAddNotification, commitRemoveNotification } from '../main/mutations';

type MainContext = ActionContext<AdminState, State>;

export const actions = {
    async actionGetRoles(context: MainContext) {
        try {
            const response = await api.getRoles(context.rootState.main.token);
            if (response) {
                commitSetRoles(context, response.data);
            }
        } catch (error) {
            await dispatchCheckApiError(context, error);
        }
    },
    async actionGetUsers(context: MainContext) {
        try {
            const response = await api.getUsers(context.rootState.main.token);
            if (response) {
                commitSetUsers(context, response.data);
            }
        } catch (error) {
            await dispatchCheckApiError(context, error);
        }
    },
    async actionUpdateUser(context: MainContext, payload: { user: IUserProfile }) {
        const loadingNotification = { content: 'saving', showProgress: true };
        try {
            commitAddNotification(context, loadingNotification);
            const response = await api.updateUser(context.rootState.main.token, payload.user);
            commitSetUser(context, response.data);
            commitRemoveNotification(context, loadingNotification);
            commitAddNotification(context, { content: 'User successfully updated', color: 'success' });
        } catch (error) {
            commitRemoveNotification(context, loadingNotification);
            commitAddNotification(context, { content: error.response.status + ' ' + error.response.data.detail, color: 'error' });
            await dispatchCheckApiError(context, error);
            throw new Error(error.response.data.detail);
        }
    },
    async actionCreateUser(context: MainContext, payload: IUserProfileCreate) {
        const loadingNotification = { content: 'saving', showProgress: true };
        try {
            commitAddNotification(context, loadingNotification);
            const response = await api.createUser(context.rootState.main.token, payload);
            commitSetUser(context, response.data);
            commitRemoveNotification(context, loadingNotification);
            commitAddNotification(context, { content: 'User successfully created', color: 'success' });
        } catch (error) {
            commitRemoveNotification(context, loadingNotification);
            commitAddNotification(context, { content: error.response.status + ' ' + error.response.data.detail, color: 'error' });
            await dispatchCheckApiError(context, error);
            throw new Error(error.response.data.detail);
        }
    },
    async actionDeleteUser(context: MainContext, payload: {login: string}) {
        const loadingNotification = { content: 'saving', showProgress: true };
        try {
            commitAddNotification(context, loadingNotification);
            const response = await api.deleteUser(context.rootState.main.token, payload.login);
            commitSetUser(context, response.data);
            commitRemoveNotification(context, loadingNotification);
            commitAddNotification(context, { content: 'Successfully deleted', color: 'success' });
        } catch (error) {
            commitRemoveNotification(context, loadingNotification);
            commitAddNotification(context, { content: error.response.status + ' ' + error.response.data.detail, color: 'error' });
            await dispatchCheckApiError(context, error);
            throw new Error(error.response.data.detail);
        }
    },
};

const { dispatch } = getStoreAccessors<AdminState, State>('');

export const dispatchCreateUser = dispatch(actions.actionCreateUser);
export const dispatchGetUsers = dispatch(actions.actionGetUsers);
export const dispatchUpdateUser = dispatch(actions.actionUpdateUser);
export const dispatchDeleteUser = dispatch(actions.actionDeleteUser);
export const dispatchGetRoles = dispatch(actions.actionGetRoles);
