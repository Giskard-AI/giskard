import {
    DatasetDTO,
    JobDTO,
    ModelDTO,
    TestCatalogDTO,
    TestSuiteExecutionDTO,
    TestSuiteNewDTO
} from '@/generated-sources';
import {defineStore} from 'pinia';
import {api} from '@/api';
import {chain} from 'lodash';
import {trackJob} from '@/utils/job-utils';
import {useMainStore} from '@/stores/main';

interface State {
    projectId: number | null,
    inputs: { [name: string]: string },
    suite: TestSuiteNewDTO | null,
    registry: TestCatalogDTO | null,
    datasets: { [key: string]: DatasetDTO },
    models: { [key: string]: ModelDTO },
    executions: TestSuiteExecutionDTO[],
    trackedJobs: { [uuid: string]: JobDTO }
}

const mainStore = useMainStore();

export const useTestSuiteStore = defineStore('testSuite', {
    state: (): State => ({
        projectId: null,
        inputs: {},
        suite: null,
        registry: null,
        datasets: {},
        models: {},
        executions: [],
        trackedJobs: {}
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
                .value();
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
        },
        async trackJob(uuid: string) {
            console.log(uuid);
            const result = await trackJob(uuid, (res) => this.trackedJobs = {
                ...this.trackedJobs,
                [uuid]: res
            });

            const res = {...this.trackedJobs};
            delete res[uuid]
            this.trackedJobs = res;

            if (result) {
                mainStore.addNotification({
                    content: 'Test suite execution has been executed successfully',
                    color: 'success'
                });
            } else {
                mainStore.addNotification({
                    content: 'An error has happened during the test suite execution',
                    color: 'error'
                });
            }

            await this.reload();
        }
    }
});
