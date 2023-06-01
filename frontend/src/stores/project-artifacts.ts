import {DatasetDTO, ModelDTO} from '@/generated-sources';
import {defineStore} from 'pinia';
import {useMainStore} from '@/stores/main';
import {api} from '@/api';
import {TYPE} from "vue-toastification";

interface State {
  projectId: number | null;
  datasets: DatasetDTO[];
  models: ModelDTO[];
}

export const useProjectArtifactsStore = defineStore('projectArtifacts', {
  state: (): State => ({
    projectId: null,
    datasets: [],
    models: [],
  }),
  getters: {},
  actions: {
    async setProjectId(projectId: number, displayNotification: boolean = true) {
      this.projectId = projectId;
      await this.loadProjectArtifacts(displayNotification);
    },
    async loadDatasetsWithNotification() {
      if (this.projectId === null) return;
      const mainStore = useMainStore();
      const loadingNotification = { content: 'Loading datasets', showProgress: true };
      try {
        mainStore.addNotification(loadingNotification);
        await this.loadDatasets();
        mainStore.removeNotification(loadingNotification);
      } catch (error) {
        mainStore.removeNotification(loadingNotification);
        mainStore.addNotification({content: `Error: ${error.message}`, color: TYPE.ERROR});
        await mainStore.checkApiError(error);
      }
    },
    async loadDatasets() {
      if (this.projectId === null) return;
      this.datasets = await api.getProjectDatasets(this.projectId!);
      this.datasets.sort((a, b) => (new Date(a.createdDate) < new Date(b.createdDate) ? 1 : -1));
    },
    async loadModelsWithNotification() {
      if (this.projectId === null) return;
      const mainStore = useMainStore();
      const loadingNotification = { content: 'Loading models', showProgress: true };
      try {
        mainStore.addNotification(loadingNotification);
        await this.loadModels();
        mainStore.removeNotification(loadingNotification);
      } catch (error) {
        mainStore.removeNotification(loadingNotification);
        mainStore.addNotification({content: `Error: ${error.message}`, color: TYPE.ERROR});
        await mainStore.checkApiError(error);
      }
    },
    async loadModels() {
      if (this.projectId === null) return;
      this.models = await api.getProjectModels(this.projectId!);
      this.models.sort((a, b) => (new Date(a.createdDate) < new Date(b.createdDate) ? 1 : -1));
    },
    async loadProjectArtifacts(displayNotification: boolean = true) {
      if (this.projectId === null) return;

      if (displayNotification) {
        const mainStore = useMainStore();
        const loadingNotification = { content: 'Loading project artifacts', showProgress: true };
        try {
          mainStore.addNotification(loadingNotification);
          await this.loadDatasets();
          await this.loadModels();
          mainStore.removeNotification(loadingNotification);
        } catch (error) {
          mainStore.removeNotification(loadingNotification);
          mainStore.addNotification({content: `Error: ${error.message}`, color: TYPE.ERROR});
          await mainStore.checkApiError(error);
        }
      } else {
        await this.loadDatasets();
        await this.loadModels();
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
    },
  },
});
