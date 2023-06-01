<template>
  <TestSuiteExecutionOverview :execution="latestExecution"/>
</template>

<script setup lang="ts">
import {useTestSuiteStore} from '@/stores/test-suite';
import {storeToRefs} from 'pinia';
import {computed} from 'vue';
import TestSuiteExecutionOverview from '@/views/main/project/TestSuiteExecutionOverview.vue';

const {executions} = storeToRefs(useTestSuiteStore());

const latestExecution = computed(() => executions.value.length === 0 ? null : executions.value[0]);

</script>

<style scoped lang="scss">
.log-viewer {
  overflow: auto;
  max-height: 400px;
}
</style>
