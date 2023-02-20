import {DatasetDTO, ModelDTO, TestCatalogDTO, TestSuiteExecutionDTO, TestSuiteNewDTO} from '@/generated-sources';
import {defineStore} from 'pinia';
import {api} from '@/api';
import {chain} from 'lodash';

interface State {
    projectId: number | null,
    inputs: { [name: string]: string },
    suite: TestSuiteNewDTO | null,
    registry: TestCatalogDTO | null,
    datasets: { [key: string]: DatasetDTO },
    models: { [key: string]: ModelDTO },
    executions: TestSuiteExecutionDTO[]
}

export const useTestSuiteStore = defineStore('testSuite', {
    state: (): State => ({
        projectId: null,
        inputs: {},
        suite: null,
        registry: null,
        datasets: {},
        models: {},
        executions: []
    }),
    getters: {
        suiteId: ({suite}) => suite === null ? null : suite.id,
        testSuiteResults: ({executions}) => {
            if (!executions) {
                return {};
            }

            return chain(executions)
                .map(execution => (execution.results ?? []).map(
                    result => ({
                        testResult: result,
                        testSuiteResult: execution
                    })
                ))
                .flatten()
                .groupBy(result => result.testResult.test.testId)
                .values();
        }
    },
    actions: {
        async reload() {
            if (this.suiteId !== null && this.projectId !== null) {
                await this.loadTestSuite(this.projectId, this.suiteId)
            }
        },
        async loadTestSuite(projectId: number, suiteId: number) {
            const [
                inputs,
                suite,
                registry,
                datasets,
                models,
                executions
            ] = await Promise.all([
                api.getTestSuiteNewInputs(projectId, suiteId),
                api.getTestSuiteNew(projectId, suiteId),
                api.getTestsCatalog(projectId),
                api.getProjectDatasets(projectId),
                api.getProjectModels(projectId),
                api.listTestSuiteExecutions(projectId, suiteId)
            ]);
            this.projectId = projectId;
            this.inputs = inputs;
            this.suite = suite;
            this.registry = registry;
            this.datasets = Object.fromEntries(datasets.map(x => [x.id, x]));
            this.models = Object.fromEntries(models.map(x => [x.id, x]));
            this.executions = executions;
        }
    }
});
