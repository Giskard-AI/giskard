import { defineStore } from 'pinia';
import { AdminUserDTO, RoleDTO } from '@/generated-sources';
import { api } from '@/api';
import { useMainStore } from '@/stores/main';
import { useUserStore } from '@/stores/user';
import { TYPE } from 'vue-toastification';
import AdminUserDTOWithPassword = AdminUserDTO.AdminUserDTOWithPassword;


interface AdminState {
    users: AdminUserDTO[],
    roles: RoleDTO[]
}

export const useAdminStore = defineStore('admin', {
    state: (): AdminState => ({
        users: [],
        roles: []
    }),
    getters: {},
    actions: {
        getUser(id: number) {
            const filteredUsers = this.users.filter((user) => user.id === id);
            if (filteredUsers.length > 0) {
                return {...filteredUsers[0]};
            }
        },

        setUser(user: AdminUserDTO) {
            const users = this.users.filter((u: AdminUserDTO) => u.id !== user.id);
            users.push(user);
            this.users = users;
        },

        async getRoles() {
            const mainStore = useMainStore();
            try {
                this.roles = await api.getRoles();
            } catch (err) {
                await mainStore.checkApiError(err);
            }
        },

        async getUsers() {
            const mainStore = useMainStore();
            try {
                this.users = await api.getUsers();
            } catch (err) {
                await mainStore.checkApiError(err);
            }
        },

        async updateUser(payload: { user: Partial<AdminUserDTOWithPassword> }) {
            const mainStore = useMainStore();
            const loadingNotification = {content: 'Saving', showProgress: true};
            try {
                mainStore.addNotification(loadingNotification);
                const response = await api.updateUser(payload.user);
                this.setUser(response);
                mainStore.removeNotification(loadingNotification);
                mainStore.addNotification({content: 'User successfully updated', color: TYPE.SUCCESS});
            } catch (error) {
                await mainStore.checkApiError(error);
                throw new Error(error.response.data.detail);
            }
        },

        async createUser(user: AdminUserDTOWithPassword) {
            const mainStore = useMainStore();
            const loadingNotification = {content: 'Saving', showProgress: true};
            try {
                mainStore.addNotification(loadingNotification);
                const response = await api.createUser(user);
                this.setUser(response);
                mainStore.removeNotification(loadingNotification);
                mainStore.addNotification({content: 'User successfully created', color: TYPE.SUCCESS});
            } catch (error) {
                await mainStore.checkApiError(error);
                throw new Error(error.response.data.detail);
            }
        },

        async disableUser(user: AdminUserDTOWithPassword) {
            const mainStore = useMainStore();
            const userStore = useUserStore();
            const loadingNotification = { content: 'Saving', showProgress: true };
            try {
                mainStore.addNotification(loadingNotification);
                await api.disableUser(user.user_id!);
                await this.getUsers();
                mainStore.removeNotification(loadingNotification);
                mainStore.addNotification({ content: 'Successfully disabled', color: TYPE.SUCCESS });

                // If we disabled ourselves, we want to logout as our user no longer exists.
                if (userStore.userProfile?.id === user.id) {
                    await userStore.logout();
                }
            } catch (error) {
                await mainStore.checkApiError(error);
                throw new Error(error.response.data.detail);
            }
        },

        async deleteUser(user: AdminUserDTOWithPassword) {
            const mainStore = useMainStore();
            const userStore = useUserStore();
            const loadingNotification = { content: 'Deleting', showProgress: true };
            try {
                mainStore.addNotification(loadingNotification);
                await api.deleteUser(user.user_id!);
                await this.getUsers();
                mainStore.removeNotification(loadingNotification);
                mainStore.addNotification({ content: 'Successfully deleted', color: TYPE.SUCCESS });

                // If we deleted ourselves, we want to logout as our user no longer exists.
                if (userStore.userProfile?.id === user.id) {
                    await userStore.logout();
                }
            } catch (error) {
                await mainStore.checkApiError(error);
                throw new Error(error.response.data.detail);
            }
        },

        async enableUser(user: AdminUserDTOWithPassword) {
            const mainStore = useMainStore();
            const loadingNotification = { content: 'Saving', showProgress: true };
            try {
                mainStore.addNotification(loadingNotification);
                await api.enableUser(user.user_id!);
                await this.getUsers();
                mainStore.removeNotification(loadingNotification);
                mainStore.addNotification({ content: 'Successfully restored', color: TYPE.SUCCESS });
            } catch (error) {
                await mainStore.checkApiError(error);
                throw new Error(error.response.data.detail);
            }
        }
    }
});
