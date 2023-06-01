<template>
  <div>
      <v-breadcrumbs
          :items="executionBreadcrumbs"
      ></v-breadcrumbs>
    <v-progress-linear
        indeterminate
        v-if="props.executions === undefined"
        color="primary"
        class="mt-2"
    ></v-progress-linear>
    <p v-else-if="props.executions.length === 0">No execution has been performed yet!</p>
    <v-row v-else>
      <v-col cols="3">
        <v-list three-line>
          <v-list-item-group v-model="selectedExecution" color="primary" mandatory>
            <template v-for="execution in props.executions">
              <v-divider/>
              <v-list-item :value="execution" :disabled="!execution.completionDate">
                <v-list-item-content>
                  <v-list-item-title>
                    <div class="d-flex justify-space-between">
                      <span>{{ execution.executionDate | moment('MMM Do YY, h:mm:ss a') }}</span>
                      <TestResultHeatmap :results="executionResults(execution)"/>
                    </div>
                  </v-list-item-title>
                  <v-list-item-subtitle>
                    <v-chip class="mr-2" x-small :color="executionStatusColor(execution)">
                      {{ executionStatusMessage(execution) }}
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
          <p class="pt-4 text-h6">Results</p>
          <TestSuiteExecutionResults :execution="selectedExecution" :registry="props.registry"
                                     :models="props.models" :datasets="props.datasets"/>
        </div>
      </v-col>
    </v-row>
  </div>
</template>

<script setup lang="ts">

import {computed, ref} from 'vue';
import {DatasetDTO, ModelDTO, TestCatalogDTO, TestResult, TestSuiteExecutionDTO} from '@/generated-sources';
import TestSuiteExecutionResults from '@/views/main/project/TestSuiteExecutionResults.vue';
import TestInputList from '@/components/TestInputList.vue';
import TestResultHeatmap from '@/components/TestResultHeatmap.vue';
import moment from 'moment';
import useRouterParamSynchronization from '@/utils/use-router-param-synchronization';

const props = defineProps<{
  projectId: number,
  suiteId: number,
  registry: TestCatalogDTO,
  models: { [key: string]: ModelDTO },
  datasets: { [key: string]: DatasetDTO },
  inputTypes: { [name: string]: string },
  executions?: TestSuiteExecutionDTO[]
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
      return "in progress";
  }
}

function executionStatusColor(execution: TestSuiteExecutionDTO): string {
  switch (execution.result) {
    case TestResult.PASSED:
      return "#4caf50";
    case TestResult.ERROR:
    case TestResult.FAILED:
      return "#f44336";
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

useRouterParamSynchronization('test-suite-new-execution', 'executionId', props.executions, selectedExecution, 'id');

</script>
