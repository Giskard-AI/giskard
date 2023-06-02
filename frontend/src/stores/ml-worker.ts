import { defineStore } from 'pinia';
import { api } from '@/api';

interface State {
  isExternalWorkerConnected: boolean;
}

export const useMLWorkerStore = defineStore('ml-worker', {
  state: (): State => ({
    isExternalWorkerConnected: false,
  }),
  getters: {},
  actions: {
    async checkExternalWorkerConnection() {
      try {
        this.isExternalWorkerConnected = await api.isExternalMLWorkerConnected();
      } catch (error) {
        console.error(error);
      }
    },
  },
});
