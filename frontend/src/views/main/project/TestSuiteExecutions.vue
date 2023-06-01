<template>
  <div>
    <div class="d-flex justify-space-between align-center">
      <v-breadcrumbs
          :items="executionBreadcrumbs"
      ></v-breadcrumbs>
      <v-btn text color="secondary" :to="{name: 'test-suite-new-compare-executions'}">
        Compare executions
        <v-icon>compare</v-icon>
      </v-btn>
    </div>
    <v-progress-linear
        indeterminate
        v-if="executionsAndJobs === undefined"
        color="primary"
        class="mt-2"
    ></v-progress-linear>
    <p v-else-if="executionsAndJobs.length === 0">No execution has been performed yet!</p>
    <v-row v-else>
      <v-col cols="3">
        <v-list three-line>
          <v-list-item-group color="primary" mandatory>
            <template v-for="e in executionsAndJobs">
              <v-divider/>
              <v-list-item v-if="e.disabled" disabled>
                <v-list-item-content>
                  <v-list-item-title>
                      {{ e.date | moment('MMM Do YY, h:mm:ss a') }}
                  </v-list-item-title>
                  <v-list-item-subtitle>
                    <v-chip class="mr-2" x-small :color="e.color">
                      {{ e.state }}
                    </v-chip>
                  </v-list-item-subtitle>
                </v-list-item-content>
              </v-list-item>
              <v-list-item v-else
                           :to="{name: 'test-suite-new-execution', params: {executionId: e.execution.id}}">
                <v-list-item-content>
                  <v-list-item-title>
                    <div class="d-flex justify-space-between">
                      <span>{{ e.execution.executionDate | moment('MMM Do YY, h:mm:ss a') }}</span>
                      <TestResultHeatmap :results="executionResults(e.execution)"/>
                    </div>
                  </v-list-item-title>
                  <v-list-item-subtitle>
                    <v-chip class="mr-2" x-small :color="e.color">
                      {{ e.state }}
                    </v-chip>
                  </v-list-item-subtitle>
                </v-list-item-content>
              </v-list-item>
            </template>
          </v-list-item-group>
        </v-list>
      </v-col>
      <v-col v-if="selectedExecution">
        <div class="pl-4">
          <p class="text-h6">Global inputs</p>
          <TestInputList :models="props.models" :inputs="selectedExecution.inputs"
                         :input-types="props.inputTypes" :datasets="props.datasets"/>
          <div v-if="selectedExecution.result === TestResult.ERROR">
            <p class="pt-4 text-h6">Error</p>
            <p>{{ selectedExecution.message }}</p>
          </div>
          <div v-else>
            <p class="pt-4 text-h6">Results</p>
            <TestSuiteExecutionResults :execution="selectedExecution" :registry="props.registry"
                                       :models="props.models" :datasets="props.datasets"/>
          </div>

        </div>
      </v-col>
    </v-row>
  </div>
</template>

<script setup lang="ts">

import {computed, ref, toRef} from 'vue';
import {
  DatasetDTO,
  JobDTO,
  JobState,
  ModelDTO,
  TestFunctionDTO,
  TestResult,
  TestSuiteExecutionDTO
} from '@/generated-sources';
import TestSuiteExecutionResults from '@/views/main/project/TestSuiteExecutionResults.vue';
import TestInputList from '@/components/TestInputList.vue';
import TestResultHeatmap from '@/components/TestResultHeatmap.vue';
import moment from 'moment';
import {Colors} from '@/utils/colors';
import useRouterParamSynchronization from '@/utils/use-router-param-synchronization';
import {Comparators} from '@/utils/comparators';

const props = defineProps<{
  projectId: number,
  suiteId: number,
  registry: { [testUuid: string]: TestFunctionDTO },
  models: { [key: string]: ModelDTO },
  datasets: { [key: string]: DatasetDTO },
  inputTypes: { [name: string]: string },
  executions?: TestSuiteExecutionDTO[],
  trackedExecutions: { [uuid: string]: JobDTO }
}>();

const selectedExecution = ref<TestSuiteExecutionDTO | null>(null);

function executionStatusMessage(execution: TestSuiteExecutionDTO): string {
  switch (execution.result) {
    case TestResult.PASSED:
      return "pass";
    case TestResult.ERROR:
      return "error";
    case TestResult.FAILED:
      return "fail";
    default:
      return "N/A";
  }
}

function jobStatusMessage(job: JobDTO): string {
  switch (job.state) {
    case JobState.SCHEDULED:
      return "scheduled";
    case JobState.RUNNING:
      return "running";
    default:
      return "N/A";
  }
}

function executionStatusColor(execution: TestSuiteExecutionDTO): string {
  switch (execution.result) {
    case TestResult.PASSED:
      return Colors.PASS;
    case TestResult.ERROR:
    case TestResult.FAILED:
      return Colors.FAIL;
    default:
      return "#607d8b";
  }
}

function jobStatusColor(job: JobDTO): string {
  switch (job.state) {
    case JobState.SCHEDULED:
      return "#607d8b";
    case JobState.RUNNING:
      return "#009688";
    default:
      return "#607d8b";
  }
}

const executionItem = {
  text: 'Executions',
  disabled: true
};

const executionBreadcrumbs = computed(() =>
    selectedExecution.value === null ? [executionItem] : [
      executionItem,
      {
        text: moment(selectedExecution.value.executionDate)
            .format('MMM Do YY, h:mm:ss a'),
        disabled: false
      }
    ]);

function executionResults(execution: TestSuiteExecutionDTO): boolean[] {
  return execution.results ? execution.results.map(result => result.passed) : [];
}

useRouterParamSynchronization('test-suite-new-execution', 'executionId', toRef(props, 'executions'), selectedExecution, 'id');

type ExecutionTabItem = {
  date: any,
  disabled: boolean,
  state: string,
  color: string,
  execution?: TestSuiteExecutionDTO
}

const executionsAndJobs = computed<ExecutionTabItem[] | undefined>(() => {
  if (props.executions === undefined) {
    return undefined;
  }

  return  ([] as ExecutionTabItem[])
      .concat(props.executions
          .map(e => ({
            date: e.executionDate,
            disabled: false,
            state: executionStatusMessage(e),
            color: executionStatusColor(e),
            execution: e
          })))
      .concat(Object.values(props.trackedExecutions)
          .map(j => ({
            date: j.scheduledDate,
            disabled: true,
            state: jobStatusMessage(j),
            color: jobStatusColor(j)
          })))
      .sort(Comparators.comparing(e => e.date))
      .reverse();
});

</script>
