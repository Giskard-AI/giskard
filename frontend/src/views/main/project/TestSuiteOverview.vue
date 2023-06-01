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
    <h2>Test Suite
      <v-chip x-small :color="latestExecution.result === TestResult.PASSED ? Colors.PASS : Colors.FAIL">
        {{ latestExecution.result === TestResult.PASSED ? 'passed' : 'failed' }}
      </v-chip>
    </h2>
    <v-row>
      <v-col cols="4">
        <v-card>
          <v-card-text>
            <p class="text-h6 text--primary">
              Global result
            </p>
            <p>Test results: {{ latestExecution.results.filter(r => r.passed).length }} /
              {{ latestExecution.results.length }}</p>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    <p class="pt-4 text-h6">Detailed results</p>
    <v-list-item-group>
      <template v-for="result in latestExecution.results">
        <v-divider/>
        <v-list-item :value="result">
          <v-list-item-content>
            <v-list-item-title
                v-text="getTestName(registryByUuid[result.test.testUuid])"></v-list-item-title>
            <v-list-item-subtitle>
              <v-chip class="mr-2" x-small :color="result.passed ? Colors.PASS : Colors.FAIL">
                {{ result.passed ? 'pass' : 'fail' }}
              </v-chip>
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
import {computed} from 'vue';
import {TestFunctionDTO, TestResult} from '@/generated-sources';
import {useMainStore} from '@/stores/main';
import {Colors} from '@/utils/colors';
import {chain} from 'lodash';

const {executions, registry, models, datasets} = storeToRefs(useTestSuiteStore());

const latestExecution = computed(() => executions.value.length === 0 ? null : executions.value[0]);
const registryByUuid = computed(() => chain(registry.value).keyBy('uuid').value());

const mainStore = useMainStore();

function copyLogs() {
  if (latestExecution.value?.logs) {
    navigator.clipboard.writeText(latestExecution.value.logs);
    mainStore.addNotification({content: 'Copied logs to clipboard', color: '#262a2d'});
  }
}

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
