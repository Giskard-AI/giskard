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
      <v-col cols="4" v-for="summary in testGroupSummaries">
        <v-card>
          <v-card-text>
            <p class="text-h6 text--primary">
              {{ summary.tag }} tests
            </p>
            <p>Test results: {{ summary.successCount }} / {{ summary.totalTests }}</p>
          </v-card-text>
        </v-card>
      </v-col>

    </v-row>

  </v-container>
</template>

<script setup lang="ts">
import {useTestSuiteStore} from '@/stores/test-suite';
import {storeToRefs} from 'pinia';
import {computed} from 'vue';
import {TestResult} from '@/generated-sources';
import {useMainStore} from '@/stores/main';
import {Colors} from '@/utils/colors';
import {chain} from 'lodash';

const {executions, registry} = storeToRefs(useTestSuiteStore());

const latestExecution = computed(() => executions.value.length === 0 ? null : executions.value[0]);

const testGroupSummaries = computed(() => chain(latestExecution.value?.results ?? [])
    .map(result => ({
      result,
      test: registry.value.find(test => test.uuid === result.test.testUuid)
    }))
    .flatMap(({result, test}) => test!.tags
        .filter(tag => tag !== 'giskard' && tag !== 'pickle')
        .map(tag => ({
          tag,
          result
        })))
    .groupBy('tag')
    .mapValues(res => ({
      tag: res[0].tag,
      successCount: res.filter(r => r.result.passed).length,
      totalTests: res.length
    }))
    .value());

const mainStore = useMainStore();

function copyLogs() {
  if (latestExecution.value?.logs) {
    navigator.clipboard.writeText(latestExecution.value.logs);
    mainStore.addNotification({content: 'Copied logs to clipboard', color: '#262a2d'});
  }
}
</script>

<style scoped lang="scss">
.log-viewer {
  overflow: auto;
  max-height: 400px;
}
</style>
