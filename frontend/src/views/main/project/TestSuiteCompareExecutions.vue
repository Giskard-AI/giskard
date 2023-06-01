<template>
  <v-row no-gutters>
    <v-col v-for="comparison in executionComparisons" :key="comparison.execution.id" class="pa-2" cols="auto">
      <v-card>
        <v-card-title>
          <TestSuiteExecutionHeader :execution="comparison.execution" :tests="comparison.tests" compact/>
        </v-card-title>
        <v-card-text>
          <SuiteTestExecutionList :tests="comparison.tests" compact/>
        </v-card-text>
      </v-card>
    </v-col>
  </v-row>
</template>

<script lang="ts" setup>

import {SuiteTestDTO, SuiteTestExecutionDTO, TestFunctionDTO, TestSuiteExecutionDTO} from '@/generated-sources';
import {computed, ComputedRef} from 'vue';
import {chain} from 'lodash';
import {storeToRefs} from 'pinia';
import {useTestSuiteStore} from '@/stores/test-suite';
import {useRoute} from 'vue-router/composables';
import SuiteTestExecutionList from '@/views/main/project/SuiteTestExecutionList.vue';
import TestSuiteExecutionHeader from '@/views/main/project/TestSuiteExecutionHeader.vue';

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

const selectedIds = computed(() => {
  if (route.query.latestCount) {
    return executions.value ?
        [...executions.value].splice(0, Number(route.query.latestCount))
            .map(execution => execution.id)
        : [];
  } else if (route.query.selectedIds) {
    return JSON.parse(route.query.selectedIds as string) as number[]
  } else {
    return [];
  }
})

const executionComparisons: ComputedRef<ExecutionComparison[]> = computed(() => {
  const results: ExecutionComparison[] = executions.value ?
      executions.value.filter(e => selectedIds.value.includes(e.id))
          .map(execution => ({execution} as ExecutionComparison))
      : [];

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
