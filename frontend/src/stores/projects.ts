import {ProjectDTO} from "@/generated-sources";
import {defineStore} from "pinia";

interface State {
    projects: ProjectDTO[]
}

export const useProjectsStore = defineStore('projects', {
    state: (): State => ({
        projects: []
    }),
    getters: {
        allProjects: (state: State) => state.projects,
        project: (state: State) => (id: number) => {
            const filtered = state.projects.filter((p) => p.id === id);
            if (filtered.length > 0) return filtered[0];
            else return undefined;
        },
    },
    actions: {
        setProject(payload: ProjectDTO) {
            const projects = this.projects.filter((p: ProjectDTO) => p.id !== payload.id);
            projects.push(payload);
            this.projects = projects;
        },
    }
});