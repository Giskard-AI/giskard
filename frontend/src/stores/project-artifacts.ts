import { DatasetDTO, ModelDTO } from "@/generated-sources";
import { defineStore } from "pinia";
import { useMainStore } from "@/stores/main";
import { api } from "@/api";

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
            const mainStore = useMainStore();
            const loadingNotification = {content: 'Loading project artifacts', showProgress: true};
            try {
              mainStore.addNotification(loadingNotification);
              await this.loadDatasets();
              await this.loadModels();
              mainStore.removeNotification(loadingNotification);
          } catch (error) {
              mainStore.removeNotification(loadingNotification);
              mainStore.addNotification({content: `Error: ${error.message}`, color: 'error'});
              await mainStore.checkApiError(error);
          }
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
            
