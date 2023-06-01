import { DatasetDTO, ModelDTO } from "@/generated-sources";
import {defineStore} from "pinia";
import {api} from "@/api";

interface State {
  projectId: number | null,
    datasets: DatasetDTO[],
    models: ModelDTO[]
}

export const useProjectArtifactsStore = defineStore('projectArtifacts', {
    state: (): State => ({
        projectId: null,
        datasets: [],
        models: []
    }),
    getters: {
        getProjectId: ({projectId}) => projectId,
        getDatasets: ({datasets}) => datasets,
        getModels: ({models}) => models
    },
    actions: {
        async setProjectId(projectId: number) {
            this.projectId = projectId;
            await this.loadProjectArtifacts();
        },
        async loadDatasets() {
          debugger;
          if (this.projectId === null) return;
          this.datasets = await api.getProjectDatasets(this.projectId!);
          this.datasets = this.datasets.sort((a, b) => new Date(a.createdDate) < new Date(b.createdDate) ? 1 : -1);
        },
        async loadModels() {
          if (this.projectId === null) return;
          this.models = await api.getProjectModels(this.projectId!);
        },
        async loadProjectArtifacts() {
            if (this.projectId === null) return;
            await this.loadDatasets();
            await this.loadModels();
        }
    }
});
            
