import { defineStore } from 'pinia';
import { AdminUserDTO, ManagedUserVM, UpdateMeDTO } from '@/generated-sources';
import { Role } from '@/enums';
import { api } from '@/api';
import { getLocalToken, removeLocalToken, saveLocalToken } from '@/utils';
import { useMainStore } from '@/stores/main';
import { TYPE } from 'vue-toastification';

interface State {
  token: string;
  isLoggedIn: boolean | null;
  loginError: string | null;
  userProfile: AdminUserDTO | null;
}

export const useUserStore = defineStore('user', {
  state: (): State => ({
    token: '',
    isLoggedIn: null,
    loginError: null,
    userProfile: null,
  }),
  getters: {
    hasAdminAccess(state: State) {
      return state.userProfile && state.userProfile.roles?.includes(Role.ADMIN) && state.userProfile.enabled;
    },
  },
  actions: {
    async login(payload: { username: string; password: string }) {
      const mainStore = useMainStore();
      try {
        const response = await api.logInGetToken(payload.username, payload.password);
        const idToken = response.id_token;
        if (idToken) {
          saveLocalToken(idToken);
          this.token = idToken;
          this.isLoggedIn = true;
          this.loginError = null;
          await mainStore.getUserProfile();
          await this.routeLoggedIn();
          mainStore.addNotification({ content: 'Logged in', color: TYPE.SUCCESS });
        } else {
          await this.logout();
        }
      } catch (err) {
        this.loginError = err.response.data.detail;
        await this.logout();
      }
    },
    async updateUserProfile(payload: UpdateMeDTO) {
      const mainStore = useMainStore();
      const loadingNotification = { content: 'saving', showProgress: true };
      try {
        mainStore.addNotification(loadingNotification);
        this.userProfile = await api.updateMe(payload);
        mainStore.removeNotification(loadingNotification);
        mainStore.addNotification({ content: 'Profile successfully updated', color: TYPE.SUCCESS });
      } catch (error) {
        await mainStore.checkApiError(error);
        throw new Error(error.response.data.detail);
      }
    },
    async checkLoggedIn() {
      const mainStore = useMainStore();

      const fetchUserAndAppSettings = async () => {
        const response = await api.getUserAndAppSettings();
        this.isLoggedIn = true;
        this.userProfile = response.user;
        mainStore.setAppSettings(response.app);
      };

      if (mainStore.authAvailable && !this.isLoggedIn) {
        let token = this.token || getLocalToken();
        if (token) {
          await fetchUserAndAppSettings();
        } else {
          this.removeLogin();
        }
      } else if (!this.isLoggedIn) {
        await fetchUserAndAppSettings();
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
      const mainStore = useMainStore();
      await this.logout();
      mainStore.addNotification({ content: 'Logged out', color: TYPE.SUCCESS });
    },
    async routeLogout() {
      // @ts-ignore
      const router = this.$router;
      if (router.currentRoute.path !== '/auth/login') {
        await router.push('/auth/login');
      }
    },
    async routeLoggedIn() {
      // @ts-ignore
      const router = this.$router;
      if (router.currentRoute.path === '/auth/login' || router.currentRoute.path === '/') {
        await router.push('/main');
      }
    },
    async passwordRecovery(payload: { userId: string }) {
      const mainStore = useMainStore();
      const loadingNotification = { content: 'Sending password recovery email', showProgress: true };
      try {
        mainStore.addNotification(loadingNotification);
        await api.passwordRecovery(payload.userId);
        mainStore.removeNotification(loadingNotification);
        mainStore.addNotification({ color: TYPE.SUCCESS, content: 'Password recovery link has been sent' });
        await this.logout();
      } catch (error) {
        mainStore.removeNotification(loadingNotification);
        let data = error.response.data;
        let errMessage = '';
        if (data.message === 'error.validation') {
          errMessage = data.fieldErrors.map(e => `${e.field}: ${e.message}`).join('\n');
        } else {
          errMessage = data.detail;
        }
        mainStore.addNotification({ color: TYPE.ERROR, content: errMessage });
      }
    },
    async resetPassword(payload: { password: string; token: string }) {
      const mainStore = useMainStore();
      const loadingNotification = { content: 'Resetting password', showProgress: true };
      mainStore.addNotification(loadingNotification);
      await api.resetPassword(payload.password);
      mainStore.removeNotification(loadingNotification);
      mainStore.addNotification({ color: TYPE.SUCCESS, content: 'Password successfully changed' });
      await this.logout();
    },
    async signupUser(payload: { userData: ManagedUserVM }) {
      const mainStore = useMainStore();
      const loadingNotification = { content: 'saving', showProgress: true };
      try {
        mainStore.addNotification(loadingNotification);
        await api.signupUser(payload.userData);
        mainStore.removeNotification(loadingNotification);
        mainStore.addNotification({ content: 'Success! Please proceed to login', color: TYPE.SUCCESS });
        await this.logout();
      } catch (error) {
        throw new Error(error.response.data.detail);
      }
    },
  },
});
