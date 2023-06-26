import {
    DatasetDTO,
    FunctionInputDTO,
    JobDTO,
    JobState,
    ModelDTO,
    RequiredInputDTO,
    TestResult,
    TestSuiteDTO,
    TestSuiteExecutionDTO
} from '@/generated-sources';
import { defineStore } from 'pinia';
import { api } from '@/api';
import { chain } from 'lodash';
import { trackJob } from '@/utils/job-utils';
import { useMainStore } from '@/stores/main';
import mixpanel from 'mixpanel-browser';
import { useTestSuiteCompareStore } from '@/stores/test-suite-compare';
import { TYPE } from 'vue-toastification';
import { anonymize } from '@/utils';


function resultHasStatus(status: TestResult, result?): boolean {
    return result !== undefined && result.status === status;
}

export const statusFilterOptions = [{
    label: 'All',
    filter: (_) => true
}, {
    label: 'Passed',
    filter: (result) => resultHasStatus(TestResult.PASSED, result)
}, {
    label: 'Failed',
    filter: (result) => resultHasStatus(TestResult.FAILED, result)
}, {
    label: 'Error',
    filter: (result) => resultHasStatus(TestResult.ERROR, result)
}, {
    label: 'Not executed',
    filter: (result) => result === undefined
}];

interface State {
    projectId: number | null,
    inputs: { [name: string]: RequiredInputDTO },
    suite: TestSuiteDTO | null,
    datasets: { [key: string]: DatasetDTO },
    models: { [key: string]: ModelDTO },
    executions: TestSuiteExecutionDTO[],
    tryResult: TestSuiteExecutionDTO | null,
    trackedJobs: { [uuid: string]: JobDTO },
    statusFilter: string,
    searchFilter: string
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
        trackedJobs: {},
        statusFilter: statusFilterOptions[0].label,
        searchFilter: ''
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
        hasInput: ({inputs}) => Object.keys(inputs).length > 0,
        hasJobInProgress: ({trackedJobs}) => Object.keys(trackedJobs).length > 0
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
            this.suite = await api.updateTestSuite(projectKey, testSuite);
        },
        async runTestSuite(input: Array<FunctionInputDTO>) {
            const jobUuid = await api.executeTestSuite(this.projectId!, this.suiteId!, input);

            mixpanel.track('Schedule test suite execution', {
                suiteId: this.suiteId,
                projectId: this.projectId,
                inputLength: input.length,
                tests: this.suite!.tests.map(({test, functionInputs}) => ({
                    uuid: test.uuid,
                    name: test.displayName ?? test.name,
                    inputs: Object.values(functionInputs).map(({value, ...data}) => ({
                        ...data,
                        value: anonymize(value)
                    }))
                })),
                inputs: input.map(({value, ...data}) => ({
                    ...data,
                    value: anonymize(value)
                })),
                jobUuid
            });

            return {
                trackJob: this.trackJob(jobUuid)
            };
        },
        async tryTestSuite(input: Array<FunctionInputDTO>) {
            this.tryResult = await api.tryTestSuite(this.projectId!, this.suiteId!, input);
        },
        async trackJob(uuid: string) {
            const start = new Date();

            const result = await trackJob(uuid, (res) => this.trackedJobs = {
                ...this.trackedJobs,
                [uuid]: res
            });

            const res = {...this.trackedJobs};
            delete res[uuid]
            this.trackedJobs = res;

            mixpanel.track('Executed test suite', {
                suiteId: this.suiteId,
                projectId: this.projectId,
                testLength: this.suite!.tests.length,
                executionDurationMs: new Date().getTime() - start.getTime(),
                jobUuid: uuid,
                result: result.state
            });

            if (result && result.state !== JobState.ERROR) {
                mainStore.addNotification({
                    content: 'Test suite execution has been executed successfully',
                    color: TYPE.SUCCESS
                });
            } else {
                mainStore.addNotification({
                    content: 'An error has happened during the test suite execution. Make sure the ML Worker is connected (On the settings tab) and check the suite execution logs',
                    color: TYPE.ERROR
                });
            }

            await this.reload();
        },
    }
});
