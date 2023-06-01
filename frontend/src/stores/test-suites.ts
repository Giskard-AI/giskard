import {TestSuiteDTO} from '@/generated-sources';
import {defineStore} from 'pinia';
import {api} from '@/api';

interface State {
    projectId: number | null,
    testSuites: Array<TestSuiteDTO>
}

export const useTestSuitesStore = defineStore('testSuites', {
    state: (): State => ({
        projectId: null,
        testSuites: []
    }),
    getters: {},
    actions: {
        async reload() {
            if (this.projectId !== null) {
                await this.loadTestSuites(this.projectId);
            }
        },
        async loadTestSuites(projectId: number) {
            this.projectId = projectId;
            this.testSuites = await api.getTestSuites(projectId)
        }
    }
});
