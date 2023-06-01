<template>
  <v-progress-linear
      indeterminate
      v-if="executions === null"
      color="primary"
      class="mt-2"
  ></v-progress-linear>
  <p v-else-if="executions.length === 0">No execution has been performed yet!</p>
  <v-tabs v-else vertical icons-and-text
  >
    <v-tab v-for="execution in executions">
      <v-chip class="mr-2" x-small :color="executionStatusColor(execution)">
        {{ executionStatusMessage(execution) }}
      </v-chip>
      <p>{{ execution.executionDate }}</p>
    </v-tab>
  </v-tabs>
</template>

<script setup lang="ts">

import {onMounted, ref} from 'vue';
import {TestResult, TestSuiteExecutionDTO} from '@/generated-sources';
import {api} from '@/api';

const props = defineProps<{
  projectId: number,
  suiteId: number
}>();

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
