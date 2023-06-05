<template>
  <v-row no-gutters>
    <v-col v-for="comparison in executionComparisons" :key="comparison.execution.id" class="pa-2" cols="6">
      <v-card>
        <v-card-title>
            <div class="d-flex flex-column align-left pb-4">
                <span class="input-execution">Model: {{ getModel(comparison.execution) }}</span>
                <span class="input-execution">Dataset: {{ getDataset(comparison.execution) }}</span>
            </div>
            <TestSuiteExecutionHeader :execution="comparison.execution" :tests="comparison.tests" compact
                                      :try-mode="false"/>
        </v-card-title>
        <v-card-text>
          <SuiteTestExecutionList :tests="comparison.tests" compact is-past-execution />
        </v-card-text>
      </v-card>
    </v-col>
  </v-row>
</template>

<script lang="ts" setup>

import {SuiteTestDTO, SuiteTestExecutionDTO, TestFunctionDTO, TestSuiteExecutionDTO} from '@/generated-sources';
import {computed, ComputedRef} from 'vue';
import {storeToRefs} from 'pinia';
import {statusFilterOptions, useTestSuiteStore} from '@/stores/test-suite';
import {useRoute} from 'vue-router/composables';
import SuiteTestExecutionList from '@/views/main/project/SuiteTestExecutionList.vue';
import TestSuiteExecutionHeader from '@/views/main/project/TestSuiteExecutionHeader.vue';
import {useCatalogStore} from "@/stores/catalog";
import {chain} from 'lodash';

const {executions, models, datasets, inputs, suite, statusFilter, searchFilter} = storeToRefs(useTestSuiteStore());
const {testFunctionsByUuid} = storeToRefs(useCatalogStore());

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
      .map(execution => ({ execution } as ExecutionComparison))
    : [];

  results.forEach(result => {
      result.tests = suite.value === null ? [] : suite.value!.tests
          .map(suiteTest => ({
              suiteTest,
              test: testFunctionsByUuid.value[suiteTest.testUuid],
              result: result.execution?.results?.find(result => result.test.id === suiteTest.id)
          }))
          .filter(({result}) => statusFilterOptions.find(opt => statusFilter.value === opt.label)!.filter(result))
          .filter(({suiteTest}) => {
              const test = suiteTest.test;

              const keywords = searchFilter.value.split(' ')
                  .map(keyword => keyword.trim().toLowerCase())
                  .filter(keyword => keyword !== '');
              return keywords.filter(keyword =>
                  test.name.toLowerCase().includes(keyword)
                  || test.doc?.toLowerCase()?.includes(keyword)
                  || test.displayName?.toLowerCase()?.includes(keyword)
                  || test.tags?.filter(tag => tag.includes(keyword))?.length > 0
              ).length === keywords.length;
          });
  })

  return results;
});

const modelByUuid = computed(() => chain(models.value)
  .keyBy('id')
  .value()
)

function getModel(execution: TestSuiteExecutionDTO) {
  const value = execution?.inputs?.find(e => e.type === 'BaseModel')?.value;
  if (value) {
    return modelByUuid.value[value]?.name ?? null;
  }
  return value ?? null;
}

function getDataset(execution: TestSuiteExecutionDTO) {
  const value = execution?.inputs?.find(e => e.type === 'Dataset')?.value;
  if (value) {
    return datasets.value[value]?.name ?? datasets.value[value]?.id;
  }
  return value ?? null;
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

.input-execution {
  font-size: 1rem;
  line-height: 1.5rem;
}
</style>
