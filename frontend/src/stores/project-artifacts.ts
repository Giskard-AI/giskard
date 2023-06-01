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
          this.models = this.models.sort((a, b) => new Date(a.createdDate) < new Date(b.createdDate) ? 1 : -1);
        },
        async loadProjectArtifacts() {
            if (this.projectId === null) return;
            await this.loadDatasets();
            await this.loadModels();
        },
        updateDataset(newDataset: DatasetDTO) {
          const idx = this.datasets.findIndex(dataset => dataset.id === newDataset.id);
          this.datasets[idx] = newDataset;
          this.datasets = [...this.datasets];
        },
        updateModel(newModel: ModelDTO) {
          const idx = this.models.findIndex(model => model.id === newModel.id);
          this.models[idx] = newModel;
          this.models = [...this.models];
        }
    }
});
            
