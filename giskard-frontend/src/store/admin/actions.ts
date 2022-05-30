import {api} from '@/api';
import {ActionContext} from 'vuex';
import {State} from '../state';
import {AdminState} from './state';
import {getStoreAccessors} from 'typesafe-vuex';
import {commitSetRoles, commitSetUser, commitSetUsers} from './mutations';
import {dispatchCheckApiError} from '../main/actions';
import {commitAddNotification, commitRemoveNotification} from '../main/mutations';
import {AdminUserDTO} from '@/generated-sources';
import AdminUserDTOWithPassword = AdminUserDTO.AdminUserDTOWithPassword;

type MainContext = ActionContext<AdminState, State>;

export const actions = {
    async actionGetRoles(context: MainContext) {
        try {
            commitSetRoles(context, await api.getRoles());
        } catch (error) {
            await dispatchCheckApiError(context, error);
        }
    },
    async actionGetUsers(context: MainContext) {
        try {
            commitSetUsers(context, await api.getUsers());
        } catch (error) {
            await dispatchCheckApiError(context, error);
        }
    },
    async actionUpdateUser(context: MainContext, payload: { user: Partial<AdminUserDTOWithPassword> }) {
        const loadingNotification = { content: 'saving', showProgress: true };
        try {
            commitAddNotification(context, loadingNotification);
            const response = await api.updateUser( payload.user);
            commitSetUser(context, response);
            commitRemoveNotification(context, loadingNotification);
            commitAddNotification(context, { content: 'User successfully updated', color: 'success' });
        } catch (error) {
            await dispatchCheckApiError(context, error);
            throw new Error(error.response.data.detail);
        }
    },
    async actionCreateUser(context: MainContext, payload: AdminUserDTOWithPassword) {
        const loadingNotification = { content: 'saving', showProgress: true };
        try {
            commitAddNotification(context, loadingNotification);
            const response = await api.createUser( payload);
            commitSetUser(context, response);
            commitRemoveNotification(context, loadingNotification);
            commitAddNotification(context, { content: 'User successfully created', color: 'success' });
        } catch (error) {
            await dispatchCheckApiError(context, error);
            throw new Error(error.response.data.detail);
        }
    },
    async actionDeleteUser(context: MainContext, payload: {id: number}) {
        const loadingNotification = { content: 'saving', showProgress: true };
        try {
            commitAddNotification(context, loadingNotification);
            const response = await api.deleteUser( payload.id);
            await this.actionGetUsers(context)
            commitRemoveNotification(context, loadingNotification);
            commitAddNotification(context, { content: 'Successfully deleted', color: 'success' });
        } catch (error) {
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
