<template>
  <div class="pl-4">
    <p class="text-h6">Global inputs</p>
    <TestInputList :models="models" :inputs="selectedExecution.inputs"
                   :input-types="inputs" :datasets="datasets"/>
    <div v-if="selectedExecution.result === TestResult.ERROR">
      <p class="pt-4 text-h6">Error</p>
      <p>{{ selectedExecution.message }}</p>
    </div>
    <div v-else>
      <p class="pt-4 text-h6">Results</p>
      <TestSuiteExecutionResults :execution="selectedExecution" :registry="registry"
                                 :models="models" :datasets="datasets"/>
    </div>

  </div>
</template>

<script setup lang="ts">

import {TestResult} from '@/generated-sources';
import TestSuiteExecutionResults from '@/views/main/project/TestSuiteExecutionResults.vue';
import TestInputList from '@/components/TestInputList.vue';
import {storeToRefs} from 'pinia';
import {useTestSuiteStore} from '@/stores/test-suite';
import {useRoute} from 'vue-router/composables';
import {computed} from 'vue';

const {registry, models, datasets, inputs, executions} = storeToRefs(useTestSuiteStore());

const route = useRoute();

const selectedExecution = computed(() => executions.value.find(e => e.id === route.params.executionId))

</script>
