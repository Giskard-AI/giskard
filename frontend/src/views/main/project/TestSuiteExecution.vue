<template>
  <div class="pl-4">
    <p class="text-h6">Global inputs</p>
    <TestInputList :models="models" :inputs="selectedExecution.inputs"
                   :input-types="inputs" :datasets="datasets"/>
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
          <pre class="log-viewer">{{ selectedExecution.logs }}</pre>
        </v-expansion-panel-content>
      </v-expansion-panel>
    </v-expansion-panels>
    <div v-if="selectedExecution.result === TestResult.ERROR">
      <p class="pt-4 text-h6">Error</p>
      <p>{{ selectedExecution.message }}</p>
    </div>
    <div v-else>
      <p class="pt-4 text-h6">Results</p>
      <TestSuiteExecutionResults :execution="selectedExecution" :registry="registry"
                                 :models="models" :datasets="datasets"/>
    </div>

  </div>
</template>

<script setup lang="ts">

import {TestResult} from '@/generated-sources';
import TestSuiteExecutionResults from '@/views/main/project/TestSuiteExecutionResults.vue';
import TestInputList from '@/components/TestInputList.vue';
import {storeToRefs} from 'pinia';
import {useTestSuiteStore} from '@/stores/test-suite';
import {useRoute} from 'vue-router/composables';
import {computed} from 'vue';
import {useMainStore} from '@/stores/main';

const {registry, models, datasets, inputs, executions} = storeToRefs(useTestSuiteStore());

const route = useRoute();

const selectedExecution = computed(() => executions.value.find(e => e.id == route.params.executionId))

const mainStore = useMainStore();

function copyLogs() {
  if (selectedExecution.value?.logs) {
    navigator.clipboard.writeText(selectedExecution.value.logs);
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

