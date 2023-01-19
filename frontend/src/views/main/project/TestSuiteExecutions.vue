<template>
  <v-progress-linear
      indeterminate
      v-if="executions === null"
      color="primary"
      class="mt-2"
  ></v-progress-linear>
  <p v-else-if="executions.length === 0">No execution has been performed yet!</p>
  <v-tabs v-else vertical icons-and-text v-model="tab"
  >
    <v-tab v-for="execution in executions">
      <v-chip class="mr-2" x-small :color="executionStatusColor(execution)">
        {{ executionStatusMessage(execution) }}
      </v-chip>
      <p>{{ execution.executionDate }}</p>
    </v-tab>
    <v-tabs-items v-model="tab">
      <v-tab-item v-for="execution in executions" :transition="false">
        <div class="pt-5">
          <span class="text-h6">Inputs</span>
        </div>
        <p v-for="[input, value] in Object.entries(execution.inputs)">
          {{ input }} -> {{ value }}
        </p>
        <div class="pt-5">
          <span class="text-h6">Results</span>
        </div>
        <TestSuiteExecutionResults :execution="execution"/>
      </v-tab-item>
    </v-tabs-items>
  </v-tabs>
</template>

<script setup lang="ts">

import {onMounted, ref} from 'vue';
import {TestResult, TestSuiteExecutionDTO} from '@/generated-sources';
import {api} from '@/api';
import TestSuiteExecutionResults from '@/views/main/project/TestSuiteExecutionResults.vue';

const props = defineProps<{
  projectId: number,
  suiteId: number
}>();

const tab = ref<any>(null);
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

</script>
