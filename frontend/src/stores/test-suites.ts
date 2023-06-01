import { TestSuiteDTO } from '@/generated-sources';
import { defineStore } from 'pinia';
import { api } from '@/api';

interface State {
  projectId: number | null;
  testSuites: Array<TestSuiteDTO>;
  currentTestSuiteId: number | null;
}

export const useTestSuitesStore = defineStore('testSuites', {
  state: (): State => ({
    projectId: null,
    testSuites: [],
    currentTestSuiteId: null,
  }),
  getters: {},
  actions: {
    async reload() {
      if (this.projectId !== null) {
        await this.loadTestSuites(this.projectId);
      }
    },
    async loadTestSuites(projectId: number) {
      if (this.projectId !== projectId) {
        this.projectId = projectId;
        this.currentTestSuiteId = null;
      }
      this.testSuites = await api.getTestSuites(projectId);
    },
    setCurrentTestSuiteId(suiteId: number | null) {
      this.currentTestSuiteId = suiteId;
    },
  },
});
