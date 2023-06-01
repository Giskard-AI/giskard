<template>
  <v-row no-gutters>
    <v-col v-for="comparison in executionComparisons" :key="comparison.execution.id" class="pa-2" cols="auto">
      <v-card>
        <v-card-title>{{ comparison.execution.completionDate | date }}</v-card-title>
        <v-card-text>
          <p class="text-h6">Inputs</p>
          <TestInputList :models="models" :inputs="comparison.execution.inputs"
                         :input-types="inputs" :datasets="datasets"/>
          <p class="text-h6">Test passed: {{ countPassedTests(comparison) }}</p>
          <p class="text-h6">Best performing tests: {{ countBestPerformingTests(comparison) }}</p>
          <v-list-item v-for="result in comparison.tests" :key="result.test.test.testUuid">
            <v-list-item-content>
              <v-list-item-title>{{ registryByUuid[result.test.test.testUuid].name }}</v-list-item-title>
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

import {SuiteTestExecutionDTO, TestResult, TestSuiteExecutionDTO} from '@/generated-sources';
import {computed, ComputedRef} from 'vue';
import TestInputList from '@/components/TestInputList.vue';
import {chain} from 'lodash';
import {storeToRefs} from 'pinia';
import {useTestSuiteStore} from '@/stores/test-suite';

const {executions, models, datasets, inputs, registry} = storeToRefs(useTestSuiteStore());

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
  const results: ExecutionComparison[] = executions.value ?
      executions.value
          .filter(execution => execution.result === TestResult.PASSED || execution.result === TestResult.FAILED)
          .map(execution => ({execution} as ExecutionComparison))
      : [];

  const groupedTestsResults: { [testId: string]: SuiteTestExecutionDTO[] } = chain(results)
      .map(r => r.execution.results ?? [])
      .flatten()
      .groupBy(result => result.test.testUuid)
      .value();

  const bestPerformingMetrics: { [testId: string]: number } = chain(groupedTestsResults)
      .mapValues((res) => res.map(result => result.metric).reduce((l, r) => Math.max(l, r)))
      .value();

  results.forEach(result => {
    result.tests = result.execution.results ? chain(result.execution.results)
            .keyBy(t => t.test.testUuid)
            .mapValues(t => ({
              test: t,
              best: bestPerformingMetrics[t.test.testUuid] === t.metric
            }))
            .value()
        : {};
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

const registryByUuid = computed(() => chain(registry.value).keyBy('uuid').value());

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
