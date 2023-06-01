<template>
  <v-container v-if="latestExecution === null">
    <p>No execution has been performed yet!</p>
  </v-container>
  <v-container v-else>
    <h2>
      <v-icon :color="latestExecution.result === TestResult.PASSED ? Colors.PASS : Colors.FAIL" size="40">{{
          latestExecution.result === TestResult.PASSED ? 'done' : 'close'
        }}
      </v-icon>
      Test Suite -
      <span
          v-if="latestExecution.result === TestResult.ERROR">An error arose during the execution</span>
      <span v-else-if="filteredTest.length === 0">No test match the current filter</span>
      <span v-else>success ratio {{ filteredTest.filter(({result}) => result !== undefined && result.passed).length }} / {{
          filteredTest.filter(({result}) => result !== undefined).length
        }}</span>
    </h2>
    <div class="d-flex mt-4 mb-4">
      <v-select
          v-model="statusFilter"
          label="Status"
          :items="statusFilterOptions"
          item-text="label"
          variant="underlined"
          hide-details="auto"
          dense
          class="mr-4"
      >
      </v-select>
      <v-text-field v-model="searchFilter" append-icon="search"
                    label="Search" type="text" dense></v-text-field>
    </div>
    <v-list-item-group>
      <template v-for="({result, test}) in filteredTest">
        <v-divider/>
        <v-list-item :value="result">
          <v-list-item-icon>
            <v-icon :color="getColor(result)" size="40">{{
                getIcon(result)
              }}
            </v-icon>
          </v-list-item-icon>
          <v-list-item-content>
            <v-list-item-title>
              <div class="d-flex justify-space-between">
                <span>{{ getTestName(test) }}</span>
                <div>
                  <v-tooltip v-if="result !== undefined && !result.passed">
                    <template v-slot:activator="{ on, attrs }">
                      <v-btn
                          class="ma-2"
                          text
                          icon
                          color="green"
                          disabled
                          v-bind="attrs" v-on="on"
                      >
                        <v-icon>mdi-bug</v-icon>
                      </v-btn>
                    </template>
                    <span>Debugger tools are not yet available</span>
                  </v-tooltip>

                </div>
              </div>
            </v-list-item-title>
            <v-list-item-subtitle>
              UUID: {{ test.uuid }}
            </v-list-item-subtitle>
          </v-list-item-content>
        </v-list-item>
      </template>
    </v-list-item-group>
  </v-container>
</template>

<script setup lang="ts">
import {useTestSuiteStore} from '@/stores/test-suite';
import {storeToRefs} from 'pinia';
import {computed, ref} from 'vue';
import {SuiteTestExecutionDTO, TestFunctionDTO, TestResult} from '@/generated-sources';
import {Colors} from '@/utils/colors';
import {chain} from 'lodash';

const {executions, registry, models, datasets, suite} = storeToRefs(useTestSuiteStore());

const statusFilterOptions = [{
  label: 'All',
  filter: (_) => true
}, {
  label: 'Passed',
  filter: (result) => result !== undefined && result.passed
}, {
  label: 'Failed',
  filter: (result) => result !== undefined && !result.passed
}, {
  label: 'Not executed',
  filter: (result) => result === undefined
}];

const statusFilter = ref<string>(statusFilterOptions[0].label);
const searchFilter = ref<string>("");

const latestExecution = computed(() => executions.value.length === 0 ? null : executions.value[0]);
const registryByUuid = computed(() => chain(registry.value).keyBy('uuid').value());

const filteredTest = computed(() => latestExecution.value === null ? [] : chain(suite.value!.tests)
    .map(suiteTest => ({
      suiteTest,
      test: registryByUuid.value[suiteTest.testUuid],
      result: latestExecution.value!.results?.find(result => result.test.id === suiteTest.id)
    }))
    .filter(({result}) => statusFilterOptions.find(opt => statusFilter.value === opt.label)!.filter(result))
    .filter(({test}) => {
      const keywords = searchFilter.value.split(' ')
          .map(keyword => keyword.trim().toLowerCase())
          .filter(keyword => keyword !== '');
      return keywords.filter(keyword =>
          test.name.toLowerCase().includes(keyword)
          || test.doc?.toLowerCase()?.includes(keyword)
          || test.displayName?.toLowerCase()?.includes(keyword)
      ).length === keywords.length;
    })
    .value()
);

function getTestName(test: TestFunctionDTO) {
  const tags = test.tags.filter(tag => tag !== 'giskard' && tag !== 'pickle');
  const name = test.displayName ?? test.name;

  if (tags.length === 0) {
    return name;
  } else {
    return tags.reduce((list, tag) => `${list} #${tag}`, '') + ` (${name})`;
  }
}

function getColor(result?: SuiteTestExecutionDTO): string {
  if (result === undefined) {
    return 'grey';
  } else if (result.passed) {
    return Colors.PASS;
  } else {
    return Colors.FAIL;
  }
}

function getIcon(result?: SuiteTestExecutionDTO): string {
  if (result === undefined) {
    return 'block';
  } else if (result.passed) {
    return 'done';
  } else {
    return 'close';
  }
}
</script>

<style scoped lang="scss">
.log-viewer {
  overflow: auto;
  max-height: 400px;
}
</style>
