import {ProjectDTO, ProjectPostDTO} from "@/generated-sources";
import {defineStore} from "pinia";
import {useMainStore} from "@/stores/main";
import {ref} from "vue";
import {api} from "@/api";

export const useProjectStore = defineStore('project', () => {
    const mainStore = useMainStore();

    // state
    const projects = ref<ProjectDTO[]>([]);

    // getters
    function project(id): ProjectDTO | undefined {
        const filtered = projects.value.filter((p) => p.id === id);
        if (filtered.length > 0) return filtered[0];
        else return undefined;
    }

    // actions
    function setProject(payload: ProjectDTO) {
        const projs = projects.value.filter((p: ProjectDTO) => p.id !== payload.id);
        projs.push(payload);
        projects.value = projs;
    }

    async function getProjects() {
        const loadingNotification = {content: 'Loading projects', showProgress: true};
        try {
            mainStore.addNotification(loadingNotification);
            const response = await api.getProjects();
            projects.value = response;

            mainStore.removeNotification(loadingNotification);
        } catch (error) {
            await mainStore.checkApiError(error);
        }
    }

    async function getProject(payload: { id: number }) {
        const loadingNotification = {content: 'Loading project', showProgress: true};
        try {
            mainStore.addNotification(loadingNotification);
            const response = await api.getProject(payload.id);
            setProject(response);
            mainStore.removeNotification(loadingNotification);
        } catch (error) {
            await mainStore.checkApiError(error);
        }
    }

    async function createProject(payload: ProjectPostDTO) {
        const loadingNotification = {content: 'Saving...', showProgress: true};
        try {
            mainStore.addNotification(loadingNotification);
            await api.createProject(payload);
            mainStore.removeNotification(loadingNotification);
            mainStore.addNotification({content: 'Success', color: 'success'});
            await getProjects();
        } catch (error) {
            await mainStore.checkApiError(error);
            throw new Error(error.response.data.detail);
        }
    }

    async function deleteProject(payload: { id: number }) {
        const loadingNotification = {content: 'Deleting...', showProgress: true};
        try {
            mainStore.addNotification(loadingNotification);
            await api.deleteProject(payload.id);
            mainStore.removeNotification(loadingNotification);
            mainStore.addNotification({content: 'Success', color: 'success'});
        } catch (error) {
            await mainStore.checkApiError(error);
        }
    }

    async function editProject(payload: { id: number, data: ProjectPostDTO }) {
        const loadingNotification = {content: 'Deleting...', showProgress: true};
        try {
            mainStore.addNotification(loadingNotification);
            const response = await api.editProject(payload.id, payload.data);
            mainStore.removeNotification(loadingNotification);
            mainStore.addNotification({content: 'Success', color: 'success'});
            setProject(response);
        } catch (error) {
            mainStore.removeNotification(loadingNotification);

            await mainStore.checkApiError(error);
        }
    }

    async function inviteUserToProject(payload: { projectId: number, userId: number }) {
        const loadingNotification = {content: 'Sending...', showProgress: true};
        try {
            mainStore.addNotification(loadingNotification);
            const response = await api.inviteUserToProject(payload.projectId, payload.userId);
            mainStore.removeNotification(loadingNotification);
            mainStore.addNotification({content: 'Done', color: 'success'});
            setProject(response);
        } catch (error) {
            await mainStore.checkApiError(error);
            throw new Error(error.response.data.detail);
        }
    }

    async function uninviteUserFromProject(payload: { projectId: number, userId: number }) {
        const loadingNotification = {content: 'Sending...', showProgress: true};
        try {
            mainStore.addNotification(loadingNotification);
            const response = await api.uninviteUserFromProject(payload.projectId, payload.userId);
            setProject(response);
            mainStore.removeNotification(loadingNotification);
            mainStore.addNotification({content: 'Done', color: 'success'});
        } catch (error) {
            mainStore.removeNotification(loadingNotification);

            await mainStore.checkApiError(error);
            throw new Error(error.response.data.detail);
        }
    }

    return { projects, project, getProjects, getProject, createProject, deleteProject, editProject, inviteUserToProject, uninviteUserFromProject }
});