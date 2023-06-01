<template>
  <div>
    <div class="d-flex justify-space-between">
      <v-breadcrumbs
          :items="executionBreadcrumbs"
      ></v-breadcrumbs>
      <v-btn text @click="loadExecutions()" color="secondary">Reload
        <v-icon right>refresh</v-icon>
      </v-btn>
    </div>
    <v-progress-linear
        indeterminate
        v-if="executions === null"
        color="primary"
        class="mt-2"
    ></v-progress-linear>
    <p v-else-if="executions.length === 0">No execution has been performed yet!</p>
    <v-row v-else>
      <v-col cols="3">
        <v-list three-line>
          <v-list-item-group v-model="selectedExecution" color="primary" mandatory>
            <template v-for="execution in executions">
              <v-divider/>
              <v-list-item :value="execution" :disabled="!execution.completionDate">
                <v-list-item-content>
                  <v-list-item-title v-text="execution.executionDate"></v-list-item-title>
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

import {computed, onMounted, ref} from 'vue';
import {DatasetDTO, ModelDTO, TestCatalogDTO, TestResult, TestSuiteExecutionDTO} from '@/generated-sources';
import {api} from '@/api';
import TestSuiteExecutionResults from '@/views/main/project/TestSuiteExecutionResults.vue';

const props = defineProps<{
  projectId: number,
  suiteId: number,
  registry: TestCatalogDTO,
  models: { [key: string]: ModelDTO },
  datasets: { [key: string]: DatasetDTO },
  inputs: { [name: string]: string }
}>();

const selectedExecution = ref<TestSuiteExecutionDTO | null>(null);
const executions = ref<TestSuiteExecutionDTO[] | null>(null);

onMounted(() => loadExecutions());

async function loadExecutions() {
  executions.value = null;
  executions.value = await api.listTestSuiteExecutions(props.projectId, props.suiteId);
}

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

function formatInputValue(input: string, value: string): string {
  switch (props.inputs[input]) {
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
        text: selectedExecution.value.executionDate,
        disabled: false
      }
    ]);

</script>
