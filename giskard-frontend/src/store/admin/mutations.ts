import { AdminState } from './state';
import { getStoreAccessors } from 'typesafe-vuex';
import { State } from '../state';
import { AdminUserDTO, RoleDTO } from '@/generated-sources';
import AdminUserDTOMigration = AdminUserDTO.AdminUserDTOMigration;

export const mutations = {
    setUsers(state: AdminState, payload: AdminUserDTOMigration[]) {
        state.users = payload;
    },
    setUser(state: AdminState, payload: AdminUserDTOMigration) {
        const users = state.users.filter((user: AdminUserDTOMigration) => user.id !== payload.id);
        users.push(payload);
        state.users = users;
    },
    setRoles(state: AdminState, payload: RoleDTO[]) {
        state.roles = payload;
    },
};

const { commit } = getStoreAccessors<AdminState, State>('');

export const commitSetUser = commit(mutations.setUser);
export const commitSetUsers = commit(mutations.setUsers);
export const commitSetRoles = commit(mutations.setRoles);
