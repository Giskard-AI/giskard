<template>
  <div class="vc">
    <v-container class="main-container vc">
      <v-progress-linear indeterminate v-if="executionsAndJobs === undefined" color="primary" class="mt-2"></v-progress-linear>
      <v-container v-else-if="executionsAndJobs.length === 0 && hasTest" class="d-flex flex-column vc fill-height">
          <h1 class="pt-16">No execution has been performed yet!</h1>
          <v-btn tile class='mx-1' @click='openRunTestSuite(false)' color="primary" :loading="hasJobInProgress">
              <v-icon>arrow_right</v-icon>
              Run test suite
          </v-btn>
      </v-container>
      <v-container v-else-if="executionsAndJobs.length === 0" class="d-flex flex-column vc fill-height">
        <h1 class="pt-16">No tests has been added to the suite</h1>
        <v-btn tile color="primaryLight" class='mx-1 primaryLightBtn' :to="{ name: 'project-catalog-tests', query: { suiteId: suite.id } }">
          <v-icon left>add</v-icon>
          Add test
        </v-btn>
      </v-container>
      <v-row v-else class="fill-height">
        <v-col cols="3" class="vc fill-height">
          <v-tooltip top>
            <template v-slot:activator="{ on, attrs }">
              <div v-bind="attrs" v-on="on">
                <v-btn text class='mx-1' @click='compare()' color="primary" :disabled="compareSelectedItems.length < 2">
                  <v-icon>compare</v-icon>
                  Compare selected executions
                </v-btn>
              </div>
            </template>
            <span v-if="compareSelectedItems.length < 2">Select at least two executions to compare</span>
            <span v-else>Show comparison of selected executions</span>
          </v-tooltip>

          <v-list three-line>
            <v-list-item-group color="primary" mandatory>
              <div v-for="e in executionsAndJobs" :key="e.execution?.id ?? e.date">
                <v-divider />
                <v-list-item :disabled="e.disabled" :to="e.disabled ? null : { name: 'test-suite-execution', params: { executionId: e.execution.id } }">
                  <v-list-item-icon>
                    <v-icon :color="e.color" size="40">{{
                      e.icon
                    }}
                    </v-icon>
                  </v-list-item-icon>
                  <v-list-item-content>
                    <div class="d-flex">
                      <div class="overflow-ellipsis">
                        <span v-if="getModel(e)">Model: {{ getModel(e) }}<br/></span>
                        <span v-if="getDataset(e)">Dataset: {{ getDataset(e) }}<br/></span>
                        <span>{{ (e.disabled ? e.date : e.execution.executionDate) | date }}</span>
                      </div>
                      <v-tooltip bottom v-if="!e.disabled">
                        <template v-slot:activator="{ on, attrs }">
                          <div v-bind="attrs" v-on="on">
                            <v-checkbox v-model="compareSelectedItems" :value="e.execution.id"/>
                          </div>
                        </template>
                        <span v-if="compareSelectedItems.includes(e.execution.id)">Remove from comparison</span>
                        <span v-else>Add to comparison</span>
                      </v-tooltip>
                    </div>
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
import {Colors} from '@/utils/colors';
import {Comparators} from '@/utils/comparators';
import {storeToRefs} from 'pinia';
import {useTestSuiteStore} from '@/stores/test-suite';
import {useRoute, useRouter} from 'vue-router/composables';
import {useTestSuiteCompareStore} from '@/stores/test-suite-compare';
import {$vfm} from 'vue-final-modal';
import RunTestSuiteModal from '@/views/main/project/modals/RunTestSuiteModal.vue';
import {chain} from "lodash";
import mixpanel from "mixpanel-browser";

const {
    models,
    datasets,
    inputs,
    executions,
    trackedJobs,
    projectId,
    suite,
    hasTest,
    hasJobInProgress
} = storeToRefs(useTestSuiteStore());


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

const route = useRoute();

const testSuiteCompareStore = useTestSuiteCompareStore()
const { compareSelectedItems } = storeToRefs(testSuiteCompareStore);

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
    router.push({ name: 'test-suite-execution', params: { executionId: executions.value[0].id.toString() } })
  }
})

async function compare() {
    await router.push({
        name: 'test-suite-compare-executions',
        query: {selectedIds: JSON.stringify(compareSelectedItems.value)}
    })

    mixpanel.track('Compare selected test suite executions', {
        suiteId: suite.value!.id,
        projectId: projectId.value,
        executionsIds: compareSelectedItems.value
    });

    testSuiteCompareStore.reset();
}

async function openRunTestSuite(compareMode: boolean) {
  await $vfm.show({
    component: RunTestSuiteModal,
    bind: {
      projectId: projectId.value,
      suiteId: suite.value!.id,
      inputs: inputs.value,
      compareMode,
      previousParams: executions.value.length === 0 ? {} : executions.value[0].inputs
    }
  });
}

const modelByUuid = computed(() => chain(models.value)
  .keyBy('id')
  .value()
)

function getDataset(e: ExecutionTabItem): string | null {
  if (e.disabled || !e.execution) {
    return null;
  }
  const value = e.execution.inputs.find(e => e.type === 'Dataset')?.value;

  if (value) {
    return datasets.value[value]?.name ?? datasets.value[value]?.id;
  }
  return value ?? null;
}

function getModel(e: ExecutionTabItem): string | null {
  if (e.disabled || !e.execution) {
    return null;
  }

  const value = e.execution.inputs.find(e => e.type === 'BaseModel')?.value;

  console.log(value);
  if (value) {
    return modelByUuid.value[value]?.name ?? null;
  }
  return value ?? null;
}

</script>

<style scoped lang="scss">
.main-container {
  width: 100%;
  max-width: 100%;
}
</style>
