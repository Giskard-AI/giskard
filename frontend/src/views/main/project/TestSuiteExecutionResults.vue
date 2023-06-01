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
                  <v-chip class="mr-2" x-small :color="result.passed ? '#4caf50' : '#f44336'">
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
        <p>metric: {{ selectedResult.metric }}</p>
        <p v-for="message in selectedResult.messages">{{ message }}</p>
      </div>
    </v-col>
  </v-row>
</template>

<script setup lang="ts">

import {ref} from 'vue';
import {TestCatalogDTO, TestExecutionDto, TestSuiteExecutionDTO} from '@/generated-sources';

const props = defineProps<{
  execution: TestSuiteExecutionDTO,
  registry: TestCatalogDTO
}>();

const selectedResult = ref<TestExecutionDto | null>(null);

</script>
