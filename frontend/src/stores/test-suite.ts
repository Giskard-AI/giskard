import {
    DatasetDTO,
    FunctionInputDTO,
    JobDTO,
    JobState,
    ModelDTO,
    RequiredInputDTO,
    TestSuiteDTO,
    TestSuiteExecutionDTO
} from '@/generated-sources';
import {defineStore} from 'pinia';
import {api} from '@/api';
import {chain} from 'lodash';
import {trackJob} from '@/utils/job-utils';
import {useMainStore} from '@/stores/main';
import mixpanel from 'mixpanel-browser';
import {useTestSuiteCompareStore} from '@/stores/test-suite-compare';
import {TYPE} from "vue-toastification";

interface State {
    projectId: number | null,
    inputs: { [name: string]: RequiredInputDTO },
    suite: TestSuiteDTO | null,
    datasets: { [key: string]: DatasetDTO },
    models: { [key: string]: ModelDTO },
    executions: TestSuiteExecutionDTO[],
    tryResult: TestSuiteExecutionDTO | null,
    trackedJobs: { [uuid: string]: JobDTO }
}

const mainStore = useMainStore();
const testSuiteCompareStore = useTestSuiteCompareStore();


export const useTestSuiteStore = defineStore('testSuite', {
    state: (): State => ({
        projectId: null,
        inputs: {},
        suite: null,
        datasets: {},
        models: {},
        executions: [],
        tryResult: null,
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
                .groupBy(result => result.testResult.test.testUuid)
                .value();
        },
        hasTest: ({suite}) => suite && Object.keys(suite.tests).length > 0,
        hasInput: ({inputs}) => Object.keys(inputs).length > 0
    },
    actions: {
        async reload() {
            if (this.suiteId !== null && this.projectId !== null) {
                await this.loadTestSuites(this.projectId, this.suiteId!);
                testSuiteCompareStore.reset()
            }
        },
        async loadTestSuites(projectId: number, suiteId: number) {
            const completeSuite = await api.getTestSuiteComplete(projectId, suiteId);

            this.projectId = projectId;
            this.inputs = completeSuite.inputs;
            this.suite = completeSuite.suite;
            this.datasets = Object.fromEntries(completeSuite.datasets.map(x => [x.id, x]));
            this.models = Object.fromEntries(completeSuite.models.map(x => [x.id, x]));
            this.executions = completeSuite.executions;
            testSuiteCompareStore.reset()
        },
        async updateTestSuite(projectKey: string, testSuite: TestSuiteDTO) {
            mixpanel.track('Update test suite v2', {
                projectKey
            });

            this.suite = await api.updateTestSuite(projectKey, testSuite);
        },
        async runTestSuite(input: Array<FunctionInputDTO>) {
            return {
                trackJob: this.trackJob(await api.executeTestSuite(this.projectId!, this.suiteId!, input))
            }
        },
        async tryTestSuite(input: Array<FunctionInputDTO>) {
            this.tryResult = await api.tryTestSuite(this.projectId!, this.suiteId!, input);

        },
        async trackJob(uuid: string) {
            const result = await trackJob(uuid, (res) => this.trackedJobs = {
                ...this.trackedJobs,
                [uuid]: res
            });

            const res = {...this.trackedJobs};
            delete res[uuid]
            this.trackedJobs = res;

            if (result && result.state !== JobState.ERROR) {
                mainStore.addNotification({
                    content: 'Test suite execution has been executed successfully',
                    color: TYPE.SUCCESS
                });
            } else {
                mainStore.addNotification({
                    content: 'An error has happened during the test suite execution',
                    color: TYPE.ERROR
                });
            }

            await this.reload();
        }
    }
});
