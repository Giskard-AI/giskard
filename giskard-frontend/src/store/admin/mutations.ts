import { AdminState } from './state';
import { getStoreAccessors } from 'typesafe-vuex';
import { State } from '../state';
import { AdminUserDTO, RoleDTO } from '@/generated-sources';
import AdminUserDTOWithPassword = AdminUserDTO.AdminUserDTOWithPassword;

export const mutations = {
    setUsers(state: AdminState, payload: AdminUserDTO[]) {
        state.users = payload;
    },
    setUser(state: AdminState, payload: AdminUserDTO) {
        const users = state.users.filter((user: AdminUserDTO) => user.id !== payload.id);
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
