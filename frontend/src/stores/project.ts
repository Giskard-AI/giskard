import {ProjectDTO, ProjectPostDTO} from "@/generated-sources";
import {defineStore} from "pinia";
import {useMainStore} from "@/stores/main";
import {api} from "@/api";

interface State {
    projects: ProjectDTO[]
}

export const useProjectStore = defineStore('project', {
    state: (): State => ({
        projects: []
    }),
    getters: {},
    actions: {
        project(id): ProjectDTO | undefined {
            const filtered = this.projects.filter((p) => p.id === id);
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
            const loadingNotification = {content: 'Loading projects', showProgress: true};
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
            const loadingNotification = {content: 'Loading project', showProgress: true};
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
            const loadingNotification = {content: 'Saving...', showProgress: true};
            try {
                mainStore.addNotification(loadingNotification);
                await api.createProject(payload);
                mainStore.removeNotification(loadingNotification);
                mainStore.addNotification({content: 'Success', color: 'success'});
                await this.getProjects();
            } catch (error) {
                await mainStore.checkApiError(error);
                throw new Error(error.response.data.detail);
            }
        },
        async deleteProject(payload: { id: number }) {
            const mainStore = useMainStore();
            const loadingNotification = {content: 'Deleting...', showProgress: true};
            try {
                mainStore.addNotification(loadingNotification);
                await api.deleteProject(payload.id);
                mainStore.removeNotification(loadingNotification);
                mainStore.addNotification({content: 'Success', color: 'success'});
            } catch (error) {
                await mainStore.checkApiError(error);
            }
        },
        async editProject(payload: { id: number, data: ProjectPostDTO }) {
            const mainStore = useMainStore();
            const loadingNotification = {content: 'Deleting...', showProgress: true};
            try {
                mainStore.addNotification(loadingNotification);
                const response = await api.editProject(payload.id, payload.data);
                mainStore.removeNotification(loadingNotification);
                mainStore.addNotification({content: 'Success', color: 'success'});
                this.setProject(response);
            } catch (error) {
                mainStore.removeNotification(loadingNotification);

                await mainStore.checkApiError(error);
            }
        },
        async inviteUserToProject(payload: { projectId: number, userId: number }) {
            const mainStore = useMainStore();
            const loadingNotification = {content: 'Sending...', showProgress: true};
            try {
                mainStore.addNotification(loadingNotification);
                const response = await api.inviteUserToProject(payload.projectId, payload.userId);
                mainStore.removeNotification(loadingNotification);
                mainStore.addNotification({content: 'Done', color: 'success'});
                this.setProject(response);
            } catch (error) {
                await mainStore.checkApiError(error);
                throw new Error(error.response.data.detail);
            }
        },
        async uninviteUserFromProject(payload: { projectId: number, userId: number }) {
            const mainStore = useMainStore();
            const loadingNotification = {content: 'Sending...', showProgress: true};
            try {
                mainStore.addNotification(loadingNotification);
                const response = await api.uninviteUserFromProject(payload.projectId, payload.userId);
                this.setProject(response);
                mainStore.removeNotification(loadingNotification);
                mainStore.addNotification({content: 'Done', color: 'success'});
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
                mainStore.addNotification({content: 'Project is being exported', color: 'success', showProgress: true});
            } catch (err) {
                await mainStore.checkApiError(err);
                throw new Error(err.response.data.detail);
            }
        }
    }
});