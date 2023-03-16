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
          <SuiteTestExecutionList :tests="comparison.tests" compact/>
        </v-card-text>
      </v-card>
    </v-col>
  </v-row>
</template>

<script lang="ts" setup>

import {SuiteTestDTO, SuiteTestExecutionDTO, TestFunctionDTO, TestSuiteExecutionDTO} from '@/generated-sources';
import {computed, ComputedRef} from 'vue';
import TestInputList from '@/components/TestInputList.vue';
import {chain} from 'lodash';
import {storeToRefs} from 'pinia';
import {useTestSuiteStore} from '@/stores/test-suite';
import {useRoute} from 'vue-router/composables';
import SuiteTestExecutionList from '@/views/main/project/SuiteTestExecutionList.vue';

const {executions, models, datasets, inputs, registry, suite} = storeToRefs(useTestSuiteStore());

type ExecutionComparison = {
  execution: TestSuiteExecutionDTO,
  tests: {
    suiteTest: SuiteTestDTO,
    test: TestFunctionDTO,
    result?: SuiteTestExecutionDTO
  }[]
}

const route = useRoute();

const executionComparisons: ComputedRef<ExecutionComparison[]> = computed(() => {
  const results: ExecutionComparison[] = executions.value ?
      [...executions.value].splice(0, Number(route.query.latestCount))
          .map(execution => ({execution} as ExecutionComparison))
      : [];

  const groupedTestsResults: { [testId: string]: SuiteTestExecutionDTO[] } = chain(results)
      .map(r => r.execution.results ?? [])
      .flatten()
      .groupBy(result => result.test.testUuid)
      .value();

  results.forEach(result => {
    result.tests = suite.value === null ? [] : suite.value!.tests
        .map(suiteTest => ({
          suiteTest,
          test: registryByUuid.value[suiteTest.testUuid],
          result: result.execution?.results?.find(result => result.test.id === suiteTest.id)
        }));
  })

  return results;
});

function countPassedTests(comparison: ExecutionComparison): number {
  return Object.values(comparison.tests)
      .filter(({result}) => result?.passed)
      .length;
}

function countBestPerformingTests(comparison: ExecutionComparison): number {
  // TODO
  return 0;
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
