<template>
  <v-container v-if="latestExecution === null">
    <p>No execution has been performed yet!</p>
  </v-container>
  <v-container v-else-if="latestExecution.result === TestResult.ERROR">
    <p>An error arose during the last test suite execution</p>
    <v-expansion-panels flat>
      <v-expansion-panel>
        <v-expansion-panel-header class="pa-0 text-h6">Logs</v-expansion-panel-header>
        <v-expansion-panel-content class="pa-0">
          <v-tooltip bottom>
            <template v-slot:activator="{ on, attrs }">
              <v-btn icon color="primary"
                     @click=copyLogs
                     v-bind="attrs"
                     v-on="on">
                <v-icon>content_copy</v-icon>
              </v-btn>
            </template>
            <span>Copy logs</span>
          </v-tooltip>
          <pre class="log-viewer">{{ latestExecution.logs }}</pre>
        </v-expansion-panel-content>
      </v-expansion-panel>
    </v-expansion-panels>
  </v-container>
  <v-container v-else>
    <h2>
      <v-icon :color="latestExecution.result === TestResult.PASSED ? Colors.PASS : Colors.FAIL" size="40">{{
          latestExecution.result === TestResult.PASSED ? 'done' : 'close'
        }}
      </v-icon>
      Test Suite
      <span v-if="filteredTest.length === 0"> - No test match the current filter</span>
      <span v-else> - success ratio {{ filteredTest.filter(test => test.passed).length }} / {{
          filteredTest.length
        }}</span>
    </h2>
    <div class="d-flex">
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
      <template v-for="result in filteredTest">
        <v-divider/>
        <v-list-item :value="result">
          <v-list-item-icon>
            <v-icon :color="result.passed ? Colors.PASS : Colors.FAIL" size="40">{{
                result.passed ? 'done' : 'close'
              }}
            </v-icon>
          </v-list-item-icon>
          <v-list-item-content>
            <v-list-item-title>
              <div class="d-flex justify-space-between">
                <span>{{ getTestName(registryByUuid[result.test.testUuid]) }}</span>
                <div>
                  <v-tooltip v-if="!result.passed">
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
              UUID: {{ result.test.testUuid }}
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
import {TestFunctionDTO, TestResult} from '@/generated-sources';
import {useMainStore} from '@/stores/main';
import {Colors} from '@/utils/colors';
import {chain} from 'lodash';

const {executions, registry, models, datasets} = storeToRefs(useTestSuiteStore());

const statusFilterOptions = [{
  label: 'All',
  filter: (_) => true
}, {
  label: 'Passed',
  filter: (result) => result.passed
}, {
  label: 'Failed',
  filter: (result) => !result.passed
}];

const statusFilter = ref<string>(statusFilterOptions[0].label);
const searchFilter = ref<string>("");

const latestExecution = computed(() => executions.value.length === 0 ? null : executions.value[0]);
const registryByUuid = computed(() => chain(registry.value).keyBy('uuid').value());

const mainStore = useMainStore();

function copyLogs() {
  if (latestExecution.value?.logs) {
    navigator.clipboard.writeText(latestExecution.value.logs);
    mainStore.addNotification({content: 'Copied logs to clipboard', color: '#262a2d'});
  }
}

const filteredTest = computed(() => latestExecution.value === null ? [] : chain(latestExecution.value.results)
    .filter(result => statusFilterOptions.find(opt => statusFilter.value === opt.label)!.filter(result))
    .filter((result) => {
      const keywords = searchFilter.value.split(' ')
          .map(keyword => keyword.trim().toLowerCase())
          .filter(keyword => keyword !== '');

      const func = registryByUuid.value[result.test.testUuid];

      return keywords.filter(keyword =>
          func.name.toLowerCase().includes(keyword)
          || func.doc?.toLowerCase()?.includes(keyword)
          || func.displayName?.toLowerCase()?.includes(keyword)
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
</script>

<style scoped lang="scss">
.log-viewer {
  overflow: auto;
  max-height: 400px;
}
</style>
