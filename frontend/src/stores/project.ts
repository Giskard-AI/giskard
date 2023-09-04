import { ProjectDTO, ProjectPostDTO } from '@/generated-sources';
import { defineStore } from 'pinia';
import { useMainStore } from '@/stores/main';
import { api } from '@/api';
import { TYPE } from 'vue-toastification';
import { useRouter } from 'vue-router';

interface State {
  projects: ProjectDTO[];
  currentProjectId: number | null;
}

export const useProjectStore = defineStore('project', {
  state: (): State => ({
    projects: [],
    currentProjectId: null,
  }),
  getters: {},
  actions: {
    project(id): ProjectDTO | undefined {
      const filtered = this.projects.filter(p => p.id === id);
      if (filtered.length > 0) return filtered[0];
      else return undefined;
    },
    setProject(payload: ProjectDTO) {
      const projects = this.projects.filter((p: ProjectDTO) => p.id !== payload.id);
      projects.push(payload);
      this.projects = projects;
    },
    async getProjects() {
      const mainStore = useMainStore();
      const loadingNotification = { content: 'Loading projects', showProgress: true };
      try {
        mainStore.addNotification(loadingNotification);
        const response = await api.getProjects();
        this.projects = response;

        mainStore.removeNotification(loadingNotification);
      } catch (error) {
        await mainStore.checkApiError(error);
      }
    },
    async getProject(payload: { id: number }) {
      const mainStore = useMainStore();
      const loadingNotification = { content: 'Loading project', showProgress: true };
      try {
        mainStore.addNotification(loadingNotification);
        const response = await api.getProject(payload.id);
        this.setProject(response);
        mainStore.removeNotification(loadingNotification);
      } catch (error) {
        await mainStore.checkApiError(error);
      }
    },
    async createProject(payload: ProjectPostDTO) {
      const mainStore = useMainStore();
      const loadingNotification = { content: 'Saving...', showProgress: true };
      // @ts-ignore
      const router = this.$router;
      try {
        mainStore.addNotification(loadingNotification);
        let response = await api.createProject(payload);
        await router.push({ name: 'project-home', params: { id: response.id.toString() } });
      } catch (error) {
        await mainStore.checkApiError(error);
        throw new Error(error.response.data.detail);
      }
    },
    async deleteProject(payload: { id: number }) {
      const mainStore = useMainStore();
      const loadingNotification = { content: 'Deleting...', showProgress: true };
      try {
        mainStore.addNotification(loadingNotification);
        await api.deleteProject(payload.id);
        mainStore.removeNotification(loadingNotification);
        mainStore.addNotification({ content: 'Success', color: TYPE.SUCCESS });
      } catch (error) {
        mainStore.removeNotification(loadingNotification);
        mainStore.addNotification({ content: `Error: ${error.message}`, color: TYPE.ERROR });
        await mainStore.checkApiError(error);
      }
    },
    async editProject(payload: { id: number; data: ProjectPostDTO }) {
      const mainStore = useMainStore();
      const loadingNotification = { content: 'Deleting...', showProgress: true };
      try {
        mainStore.addNotification(loadingNotification);
        const response = await api.editProject(payload.id, payload.data);
        mainStore.removeNotification(loadingNotification);
        mainStore.addNotification({ content: 'Success', color: TYPE.SUCCESS });
        this.setProject(response);
      } catch (error) {
        mainStore.removeNotification(loadingNotification);
        mainStore.addNotification({ content: `Error: ${error.message}`, color: TYPE.ERROR });
        await mainStore.checkApiError(error);
      }
    },
    async inviteUserToProject(payload: { projectId: number; userId: number }) {
      const mainStore = useMainStore();
      const loadingNotification = { content: 'Sending...', showProgress: true };
      try {
        mainStore.addNotification(loadingNotification);
        const response = await api.inviteUserToProject(payload.projectId, payload.userId);
        mainStore.removeNotification(loadingNotification);
        mainStore.addNotification({ content: 'Done', color: TYPE.SUCCESS });
        this.setProject(response);
      } catch (error) {
        await mainStore.checkApiError(error);
        throw new Error(error.response.data.detail);
      }
    },
    async uninviteUserFromProject(payload: { projectId: number; userId: number }) {
      const mainStore = useMainStore();
      const loadingNotification = { content: 'Sending...', showProgress: true };
      try {
        mainStore.addNotification(loadingNotification);
        const response = await api.uninviteUserFromProject(payload.projectId, payload.userId);
        this.setProject(response);
        mainStore.removeNotification(loadingNotification);
        mainStore.addNotification({ content: 'Done', color: TYPE.SUCCESS });
      } catch (error) {
        mainStore.removeNotification(loadingNotification);
        await mainStore.checkApiError(error);
        throw new Error(error.response.data.detail);
      }
    },
    async exportProject(id: number) {
      const mainStore = useMainStore();
      try {
        api.downloadExportedProject(id);
        mainStore.addNotification({
          content: 'Project is being exported',
          color: TYPE.SUCCESS,
          showProgress: true,
        });
      } catch (err) {
        await mainStore.checkApiError(err);
        throw new Error(err.response.data.detail);
      }
    },
    setCurrentProjectId(id: number | null) {
      this.currentProjectId = id;
    },
  },
});
