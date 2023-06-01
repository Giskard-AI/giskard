<template>
  <v-row>
    <v-col cols="3">
      <v-list three-line>
        <v-list-item-group v-model="selectedResult" color="primary" mandatory>
          <template v-for="result in props.execution.results">
            <v-divider/>
            <v-list-item :value="result">
              <v-list-item-content>
                <v-list-item-title v-text="registry.tests[result.test.testId].name"></v-list-item-title>
                <v-list-item-subtitle>
                  <v-chip class="mr-2" x-small :color="result.passed ? Colors.PASS : Colors.FAIL">
                    {{ result.passed ? 'pass' : 'fail' }}
                  </v-chip>
                </v-list-item-subtitle>
              </v-list-item-content>
            </v-list-item>
          </template>
        </v-list-item-group>
      </v-list>
    </v-col>
    <v-col v-if="selectedResult">
      <div class="pl-4">
        <p class="text-h6">Test inputs</p>
        <TestInputList :models="props.models" :inputs="selectedResult.inputs"
                       :input-types="inputTypes" :datasets="props.datasets"/>
        <p>metric: {{ selectedResult.metric }}</p>
        <p v-for="message in selectedResult.messages">{{ message }}</p>
      </div>
    </v-col>
  </v-row>
</template>

<script setup lang="ts">

import {computed, ref} from 'vue';
import {DatasetDTO, ModelDTO, SuiteTestExecutionDTO, TestCatalogDTO, TestSuiteExecutionDTO} from '@/generated-sources';
import TestInputList from '@/components/TestInputList.vue';
import {Colors} from '@/utils/colors';

const props = defineProps<{
  execution: TestSuiteExecutionDTO,
  registry: TestCatalogDTO,
  models: { [key: string]: ModelDTO },
  datasets: { [key: string]: DatasetDTO }
}>();

const selectedResult = ref<SuiteTestExecutionDTO | null>(null);

const inputTypes = computed(() =>
    selectedResult.value === null ? {} :
        Object.values(props.registry.tests[selectedResult.value.test.testId].arguments)
            .reduce((accumulator, currentValue) => {
              accumulator[currentValue.name] = currentValue.type;
              return accumulator;
            }, {}));

</script>
