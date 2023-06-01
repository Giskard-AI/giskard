<template>
  <div class="d-flex overflow-y-auto">
    <div v-for="execution in completedExecutions" class="execution-container">
      <p class="text-h5">{{ execution.completionDate | moment('MMM Do YY, h:mm:ss a') }}</p>
      <p class="text-h6">Inputs</p>
      <TestInputList :models="props.models" :inputs="execution.inputs"
                     :input-types="props.inputTypes" :datasets="props.datasets"/>
      <p class="text-h6">Test passed: {{ countPassedTests(execution) }}</p>
      <p class="text-h6">Best performing tests: {{ countBestPerformingTests(execution) }}</p>
    </div>
  </div>
</template>

<script lang="ts" setup>

import {DatasetDTO, ModelDTO, SuiteTestExecutionDTO, TestResult, TestSuiteExecutionDTO} from '@/generated-sources';
import {computed, ComputedRef} from 'vue';
import TestInputList from '@/components/TestInputList.vue';
import {ArrayReducers} from '@/utils/array-reducers';
import {KeyValueUtils} from '@/utils/key-value-utils';

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
        : []
);

const commonTestIds = computed(() =>
    completedExecutions.value
        .map(execution => execution.results ?? [])
        .map(results => results.map(result => result.test.testId))
        .reduce((commonTestIds, testIds) => commonTestIds.filter(commonTestId => testIds.indexOf(commonTestId) !== -1))
);

const executedTestsMap: ComputedRef<{ [id: number]: SuiteTestExecutionDTO[] }> = computed(() =>
    completedExecutions.value
        .reduce(ArrayReducers.toMap(execution => execution.id,
            execution => execution.results
                ?.filter(test => commonTestIds.value.indexOf(test.test.testId) !== -1) ?? []), {})
);

const groupedTestsResults = computed(() =>
    Object.values(executedTestsMap.value)
        .reduce((flattened, results) => flattened.concat(results), [])
        .reduce(ArrayReducers.groupBy(result => result.test.testId), {})
);

const bestPerformingMetrics = computed(() =>
    KeyValueUtils.mapValues(groupedTestsResults.value,
        results => results.map(result => result.metric).reduce((l, r) => Math.max(l, r)))
);

function countPassedTests(execution: TestSuiteExecutionDTO): number {
  return executedTestsMap.value[execution.id].filter(test => test.passed).length;
}

function countBestPerformingTests(execution: TestSuiteExecutionDTO): number {
  return executedTestsMap.value[execution.id]
      .filter(test => bestPerformingMetrics.value[test.test.testId] === test.metric)
      .length;
}

</script>

<style scoped lang="scss">
.execution-container {
  min-width: 64px;
  padding: 4px;
  margin: 4px;
  border: 2px solid #000000;
}
</style>
