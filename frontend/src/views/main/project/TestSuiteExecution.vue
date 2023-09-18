<template>
  <TestSuiteExecutionOverview v-if="selectedExecution" :execution="selectedExecution" :is-past-execution="true"/>
  <div v-else/>
</template>

<script setup lang="ts">

import {storeToRefs} from 'pinia';
import {useTestSuiteStore} from '@/stores/test-suite';
import {useRoute} from 'vue-router/composables';
import {computed} from 'vue';
import TestSuiteExecutionOverview from '@/views/main/project/TestSuiteExecutionOverview.vue';

const {executions} = storeToRefs(useTestSuiteStore());

const route = useRoute();

const selectedExecution = computed(() => executions.value.find(e => e.id == route.params.executionId))
</script>

<style scoped lang="scss">
.log-viewer {
  overflow: auto;
  max-height: 400px;
}
</style>

