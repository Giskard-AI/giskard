<template>
  <v-tabs vertical icons-and-text v-model="tab"
  >
    <v-tab v-for="result in props.execution.results">
      <v-chip class="mr-2" x-small :color="result.passed ? '#4caf50' : '#f44336'">
        {{ result.passed ? 'pass' : 'fail' }}
      </v-chip>
      <p>{{ registry.tests[result.test.testId].name }}</p>
    </v-tab>
    <v-tabs-items v-model="tab">
      <v-tab-item v-for="result in props.execution.results" :transition="false">
        <p>metric: {{ result.metric }} </p>
      </v-tab-item>
    </v-tabs-items>
  </v-tabs>
</template>

<script setup lang="ts">

import {ref} from 'vue';
import {TestCatalogDTO, TestResult, TestSuiteExecutionDTO} from '@/generated-sources';

const props = defineProps<{
  execution: TestSuiteExecutionDTO,
  registry: TestCatalogDTO
}>();

const tab = ref<any>(null);

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
