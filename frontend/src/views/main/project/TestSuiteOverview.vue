<template>
  <TestSuiteExecutionOverview :execution="displayTry ? tryResult : latestExecution" :try-mode="displayTry" :is-past-execution="false" />
</template>

<script setup lang="ts">
import {useTestSuiteStore} from '@/stores/test-suite';
import {storeToRefs} from 'pinia';
import {computed} from 'vue';
import TestSuiteExecutionOverview from '@/views/main/project/TestSuiteExecutionOverview.vue';

const {executions, tryResult} = storeToRefs(useTestSuiteStore());

const latestExecution = computed(() => executions.value.length === 0 ? null : executions.value[0]);

const displayTry = computed(() => tryResult.value && (!latestExecution.value || tryResult.value.executionDate > latestExecution.value.executionDate))

</script>

<style scoped lang="scss">
.log-viewer {
  overflow: auto;
  max-height: 400px;
}
</style>
