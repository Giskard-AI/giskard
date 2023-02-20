<template>
  <div>
    <div class="d-flex justify-space-between">
      <v-breadcrumbs
          :items="executionBreadcrumbs"
      ></v-breadcrumbs>
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
          <v-list-item-group v-model="selectedExecution" color="primary" mandatory>
            <template v-for="e in executionsAndJobs">
              <v-divider/>
              <v-list-item :value="e.execution" :disabled="e.disabled">
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
            </template>
          </v-list-item-group>
        </v-list>
      </v-col>
      <v-col v-if="selectedExecution">
        <div class="pl-4">
          <p class="text-h6">Inputs</p>
          <v-list-item v-for="[input, value] in Object.entries(selectedExecution.inputs)" :track-by="input">
            <v-list-item-content>
              <v-list-item-title>{{ input }}</v-list-item-title>
              <v-list-item-subtitle> {{ formatInputValue(input, value) }}</v-list-item-subtitle>
            </v-list-item-content>
          </v-list-item>
          <p class="pt-4 text-h6">Results</p>
          <TestSuiteExecutionResults :execution="selectedExecution" :registry="props.registry"/>
        </div>
      </v-col>
    </v-row>
  </div>
</template>

<script setup lang="ts">

import {computed, ref} from 'vue';
import {
  DatasetDTO,
  JobDTO,
  JobState,
  ModelDTO,
  TestCatalogDTO,
  TestResult,
  TestSuiteExecutionDTO
} from '@/generated-sources';
import TestSuiteExecutionResults from '@/views/main/project/TestSuiteExecutionResults.vue';
import moment from 'moment';
import {Colors} from '@/utils/colors';
import {Comparators} from '@/utils/comparators';

const props = defineProps<{
  projectId: number,
  suiteId: number,
  registry: TestCatalogDTO,
  models: { [key: string]: ModelDTO },
  datasets: { [key: string]: DatasetDTO },
  inputTypes: { [name: string]: string },
  executions?: TestSuiteExecutionDTO[],
  trackedExecutions: { [uuid: string]: JobDTO}
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

function formatInputValue(input: string, value: string): string {
  switch (props.inputTypes[input]) {
    case 'Dataset':
      return props.datasets[value].name;
    case 'Model':
      return props.models[value].name;
    default:
      return value;
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
