import { TestSuiteDTO, TestSuiteCompleteDTO } from '@/generated-sources';
import { defineStore } from 'pinia';
import { api } from '@/api';

interface State {
  projectId: number | null;
  testSuitesComplete: TestSuiteCompleteDTO[];
  testSuites: Array<TestSuiteDTO>;
  currentTestSuiteId: number | null;
}

export const useTestSuitesStore = defineStore('testSuites', {
  state: (): State => ({
    projectId: null,
    testSuitesComplete: [],
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
    async reloadComplete() {
      if (this.projectId !== null) {
        await this.loadTestSuiteComplete(this.projectId);
        await this.reload();
      }
    },
    async loadTestSuites(projectId: number) {
      if (this.projectId !== projectId) {
        this.projectId = projectId;
        this.currentTestSuiteId = null;
      }
      this.testSuites = await api.getTestSuites(projectId);
    },
    async loadTestSuiteComplete(projectId: number) {
      if (this.projectId !== projectId) {
        this.projectId = projectId;
        this.currentTestSuiteId = null;
      }
      this.testSuitesComplete = [];
      for await (const suite of this.testSuites) {
        const testSuiteComplete = await api.getTestSuiteComplete(this.projectId!, suite.id!);
        this.testSuitesComplete.push(testSuiteComplete);
      }
    },
    async updateSuiteName(suite: TestSuiteDTO) {
      await api.updateTestSuite(suite.projectKey!, suite);
      await this.reload();
    },
    setCurrentTestSuiteId(suiteId: number | null) {
      this.currentTestSuiteId = suiteId;
    },
  },
});
