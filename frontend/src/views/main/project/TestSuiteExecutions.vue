<template>
  <div class="vc">
    <div class="d-flex justify-space-between align-center">
      <v-breadcrumbs
          :items="executionBreadcrumbs"
      ></v-breadcrumbs>
      <v-btn text color="secondary" @click="handleOpenGlobalInputs">
        Global inputs
        <v-icon>info</v-icon>
      </v-btn>
    </div>
    <v-container class="main-container vc">
      <v-progress-linear
          indeterminate
          v-if="executionsAndJobs === undefined"
          color="primary"
          class="mt-2"
      ></v-progress-linear>
      <p v-else-if="executionsAndJobs.length === 0">No execution has been performed yet!</p>
      <v-row v-else class="fill-height">
        <v-col cols="3" class="vc fill-height">
          <v-list three-line>
            <v-list-item-group color="primary" mandatory>
              <div v-for="e in executionsAndJobs" :key="e.date">
                <v-divider/>
                <v-list-item v-if="e.disabled" disabled>
                  <v-list-item-icon>
                    <v-icon :color="e.color" size="40">{{
                        e.icon
                      }}
                    </v-icon>
                  </v-list-item-icon>
                  <v-list-item-content>
                    <v-list-item-title>
                      {{ e.date | date }}
                    </v-list-item-title>
                  </v-list-item-content>
                </v-list-item>
                <v-list-item v-else
                             :to="{name: 'test-suite-execution', params: {executionId: e.execution.id}}">
                  <v-list-item-icon>
                    <v-icon :color="e.color" size="40">{{
                        e.icon
                      }}
                    </v-icon>
                  </v-list-item-icon>
                  <v-list-item-content>
                    <v-list-item-title>
                      <div class="d-flex justify-space-between">
                        <span>{{ e.execution.executionDate | date }}</span>
                        <TestResultHeatmap :results="executionResults(e.execution)"/>
                      </div>
                    </v-list-item-title>
                  </v-list-item-content>
                </v-list-item>
              </div>
            </v-list-item-group>
          </v-list>
        </v-col>
        <v-col class="vc fill-height">
          <router-view></router-view>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script setup lang="ts">

import {computed, onMounted} from 'vue';
import {JobDTO, JobState, TestResult, TestSuiteExecutionDTO} from '@/generated-sources';
import TestResultHeatmap from '@/components/TestResultHeatmap.vue';
import {Colors} from '@/utils/colors';
import {Comparators} from '@/utils/comparators';
import {storeToRefs} from 'pinia';
import {useTestSuiteStore} from '@/stores/test-suite';
import {formatDate} from '@/filters';
import {useRoute, useRouter} from 'vue-router/composables';
import {$vfm} from 'vue-final-modal';
import TestSuiteExecutionInputsModal from '@/views/main/project/modals/TestSuiteExecutionInputsModal.vue';

const {registry, models, datasets, inputs, executions, trackedJobs} = storeToRefs(useTestSuiteStore());

function executionStatusMessage(execution: TestSuiteExecutionDTO): string {
  switch (execution.result) {
    case TestResult.PASSED:
      return "pass";
    case TestResult.ERROR:
      return "error";
    case TestResult.FAILED:
      return "fail";
    default:
      return "N/A";
  }
}

function executionStatusIcon(execution: TestSuiteExecutionDTO): string {
  switch (execution.result) {
    case TestResult.PASSED:
      return "done";
    case TestResult.ERROR:
      return "error";
    case TestResult.FAILED:
      return "close";
    default:
      return "sync";
  }
}

function executionStatusColor(execution: TestSuiteExecutionDTO): string {
  switch (execution.result) {
    case TestResult.PASSED:
      return Colors.PASS;
    case TestResult.ERROR:
    case TestResult.FAILED:
      return Colors.FAIL;
    default:
      return "#607d8b";
  }
}

function jobStatusColor(job: JobDTO): string {
  switch (job.state) {
    case JobState.SCHEDULED:
      return "#607d8b";
    case JobState.RUNNING:
      return "#009688";
    default:
      return "#607d8b";
  }
}

const executionItem = {
  text: 'Executions',
  disabled: true
};

const route = useRoute();

const selectedExecution = computed(() => executions.value.find(e => e.id == route.params.executionId));

const executionBreadcrumbs = computed(() =>
    !selectedExecution.value ? [executionItem] : [
      executionItem,
      {
        text: formatDate(selectedExecution.value.executionDate),
        disabled: false
      }
    ]);

function executionResults(execution: TestSuiteExecutionDTO): boolean[] {
  return execution.results ? execution.results.map(result => result.passed) : [];
}

type ExecutionTabItem = {
  date: any,
  disabled: boolean,
  color: string,
  icon: string,
  execution?: TestSuiteExecutionDTO
}

const executionsAndJobs = computed<ExecutionTabItem[] | undefined>(() => {
  if (executions.value === undefined) {
    return undefined;
  }

  return ([] as ExecutionTabItem[])
      .concat(executions.value
          .map(e => ({
            date: e.executionDate,
            disabled: false,
            color: executionStatusColor(e),
            icon: executionStatusIcon(e),
            execution: e
          })))
      .concat(Object.values(trackedJobs.value)
          .map(j => ({
            date: j.scheduledDate,
            disabled: true,
            color: jobStatusColor(j),
            icon: 'sync'
          })))
      .sort(Comparators.comparing(e => e.date))
      .reverse();
});

const router = useRouter();

onMounted(() => {
  if (executions.value.length > 0 && !route.params.executionId) {
    router.push({name: 'test-suite-execution', params: {executionId: executions.value[0].id.toString()}})
  }
})

function handleOpenGlobalInputs() {
  $vfm.show({
    component: TestSuiteExecutionInputsModal,
    bind: {
      execution: selectedExecution.value
    }
  });
}
</script>

<style scoped lang="scss">
.main-container {
  width: 100%;
  max-width: 100%;
}
</style>
