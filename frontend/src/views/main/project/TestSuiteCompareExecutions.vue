<template>
  <v-row no-gutters>
    <v-col v-for="comparison in executionComparisons" :key="comparison.execution.id" class="pa-2" cols="auto">
      <v-card>
        <v-card-title>{{ comparison.execution.completionDate | moment('MMM Do YY, h:mm:ss a') }}</v-card-title>
        <v-card-text>
          <p class="text-h6">Inputs</p>
          <TestInputList :models="props.models" :inputs="comparison.execution.inputs"
                         :input-types="props.inputTypes" :datasets="props.datasets"/>
          <p class="text-h6">Test passed: {{ countPassedTests(comparison) }}</p>
          <p class="text-h6">Best performing tests: {{ countBestPerformingTests(comparison) }}</p>
          <v-list-item v-for="result in Object.values(comparison.tests)" :key="result.test.test.testId">
            <v-list-item-content>
              <v-list-item-title>{{ registry.tests[result.test.test.testId].name }}</v-list-item-title>
              <v-list-item-subtitle><span :class="{
                passed: result.test.passed,
                failed: !result.test.passed,
                'best-performing': result.best
              }">{{ result.test.metric }}</span>
              </v-list-item-subtitle>
            </v-list-item-content>
          </v-list-item>
        </v-card-text>
      </v-card>
    </v-col>
  </v-row>
</template>

<script lang="ts" setup>

import {
  DatasetDTO,
  ModelDTO,
  SuiteTestExecutionDTO,
  TestCatalogDTO,
  TestResult,
  TestSuiteExecutionDTO
} from '@/generated-sources';
import {computed, ComputedRef} from 'vue';
import TestInputList from '@/components/TestInputList.vue';
import {KeyValueUtils} from '@/utils/key-value-utils';
import {ArrayReducers} from '@/utils/array-reducers';

const props = defineProps<{
  executions?: TestSuiteExecutionDTO[],
  models: { [key: string]: ModelDTO },
  datasets: { [key: string]: DatasetDTO },
  inputTypes: { [name: string]: string },
  registry: TestCatalogDTO,
}>();

type ExecutionComparison = {
  execution: TestSuiteExecutionDTO,
  tests: {
    [testId: string]: {
      test: SuiteTestExecutionDTO,
      best: boolean;
    }
  }
}

const executionComparisons: ComputedRef<ExecutionComparison[]> = computed(() => {
  const results: ExecutionComparison[] = props.executions ?
      props.executions
          .filter(execution => execution.result === TestResult.PASSED || execution.result === TestResult.FAILED)
          .map(execution => ({execution} as ExecutionComparison))
      : [];

  const groupedTestsResults: { [testId: string]: SuiteTestExecutionDTO[] } = results
      .map(r => r.execution.results ?? [])
      .reduce((flattened, results) => flattened.concat(results), [])
      .reduce(ArrayReducers.groupBy(result => result.test.testId), {});

  const bestPerformingMetrics: { [testId: string]: number } = KeyValueUtils.mapValues(groupedTestsResults,
      res => res.map(result => result.metric).reduce((l, r) => Math.max(l, r)))

  results.forEach(result => {
    result.tests = result.execution.results
            ?.reduce(ArrayReducers.toMap(test => test.test.testId, test => ({
              test,
              best: bestPerformingMetrics[test.test.testId] === test.metric
            })), {})
        ?? {};
  })

  return results;
});

function countPassedTests(comparison: ExecutionComparison): number {
  return Object.values(comparison.tests)
      .filter(result => result.test.passed)
      .length;
}

function countBestPerformingTests(comparison: ExecutionComparison): number {
  return Object.values(comparison.tests)
      .filter(result => result.best)
      .length;
}

</script>

<style scoped lang="scss">
.best-performing {
  font-weight: bold;
}

.passed {
  color: #4caf50;
}

.failed {
  color: #F44336;
}
</style>
