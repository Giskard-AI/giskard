<template>
  <div class="d-flex overflow-y-auto">
    <div v-for="execution in completedExecutions" class="execution-container">
      {{ execution.completionDate | moment('MMM Do YY, h:mm:ss a') }}
      <p class="text-h6">Inputs</p>
      <TestInputList :models="props.models" :inputs="execution.inputs"
                     :input-types="props.inputTypes" :datasets="props.datasets"/>
    </div>
  </div>
</template>

<script lang="ts" setup>

import {DatasetDTO, ModelDTO, TestResult, TestSuiteExecutionDTO} from '@/generated-sources';
import {computed} from 'vue';
import TestInputList from '@/components/TestInputList.vue';

const props = defineProps<{
  executions?: TestSuiteExecutionDTO[],
  models: { [key: string]: ModelDTO },
  datasets: { [key: string]: DatasetDTO },
  inputTypes: { [name: string]: string }
}>();

const completedExecutions = computed(() =>
    props.executions ?
        props.executions
            .filter(execution => execution.result === TestResult.PASSED || execution.result === TestResult.FAILED)
        : []);

</script>

<style scoped lang="scss">
.execution-container {
  min-width: 64px;
  padding: 4px;
  margin: 4px;
  border: 2px solid #000000;
}
</style>
