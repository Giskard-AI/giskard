<template>
  <v-container fluid class="vc">
    <v-row>
      <v-col :align="'right'">
        <div class="d-flex flex-row-reverse">
          <RunTestSuiteModal :inputs="inputs" :suite-id="suiteId" :project-id="projectId"
                             @uuid="onExecutionScheduled"/>
          <v-btn text @click="loadData()" color="secondary">Reload
            <v-icon right>refresh</v-icon>
          </v-btn>
        </div>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="2">
        <v-tabs vertical v-model="tab">
          <v-tab :to="{name:'test-suite-new-inputs'}">Inputs & parameters</v-tab>
          <v-tab :to="{name:'test-suite-new-tests'}">Tests</v-tab>
          <v-tab :to="{name:'test-suite-new-configuration'}">Configuration</v-tab>
          <v-tab :to="{name:'test-suite-new-execution'}">Execution</v-tab>
          <v-tab :to="{name:'test-suite-new-compare-executions'}" class="d-none">Compare executions</v-tab>
          <v-tab :to="{name:'test-suite-new-compare-test'}" class="d-none">Compare tests</v-tab>
        </v-tabs>
      </v-col>
      <v-col cols="10">
        <v-tabs-items v-model="tab">
          <router-view/>
          <v-tab-item :transition="false">
            <TestSuiteExecutions :project-id="props.projectId"
                                 :suite-id="props.suiteId"
                                 :registry="registry"
                                 :models="allModels"
                                 :datasets="allDatasets"
                                 :inputTypes="inputs"
                                 :executions="executions"
                                 :tracked-executions="trackedJobs"/>
          </v-tab-item>
          <v-tab-item :transition="false">
            <TestSuiteCompareExecutions
                :executions="executions"
                :models="allModels"
                :datasets="allDatasets"
                :inputTypes="inputs"
                :registry="registry"/>
          </v-tab-item>
          <v-tab-item :transition="false">
            <TestSuiteCompareTest
                :executions="executions"
                :registry="registry"/>
          </v-tab-item>
        </v-tabs-items>
      </v-col>
    </v-row>
  </v-container>
</template>

<script lang="ts" setup>

import {onMounted, ref, watch} from "vue";
import {DatasetDTO, ModelDTO, TestCatalogDTO, TestSuiteExecutionDTO, TestSuiteNewDTO} from "@/generated-sources";
import RunTestSuiteModal from '@/views/main/project/modals/RunTestSuiteModal.vue';
import TestSuiteExecutions from '@/views/main/project/TestSuiteExecutions.vue';
import TestSuiteCompareExecutions from '@/views/main/project/TestSuiteCompareExecutions.vue';
import TestSuiteCompareTest from '@/views/main/project/TestSuiteCompareTest.vue';
import {useTrackJob} from '@/utils/use-track-job';
import {useMainStore} from "@/stores/main";
import {useTestSuiteStore} from '@/stores/test-suite';

const props = defineProps<{
  projectId: number,
  suiteId: number
}>();

const mainStore = useMainStore();

const suite = ref<TestSuiteNewDTO | null>(null);
const registry = ref<TestCatalogDTO | null>(null);
const tab = ref<any>(null);
const inputs = ref<{ [name: string]: string }>({});
const allDatasets = ref<{ [key: string]: DatasetDTO }>({});
const allModels = ref<{ [key: string]: ModelDTO }>({});
const executions = ref<TestSuiteExecutionDTO[]>();

onMounted(() => loadData());
watch(() => props.suiteId, () => loadData());

const {loadTestSuite} = useTestSuiteStore();

async function loadData() {
  await loadTestSuite(props.projectId, props.suiteId);
}

watch(() => suite.value, () => {
  if (selectedTest.value !== null && suite.value !== null) {
    selectedTest.value = suite.value.tests.find(test => test.testId === selectedTest.value?.testId) ?? null;
  }
})


const {
  trackedJobs,
  addJob
} = useTrackJob();

async function onExecutionScheduled(jobUuid: string) {
  const result = await addJob(jobUuid);
  if (result) {
    mainStore.addNotification({content: 'Test suite execution has been executed successfully', color: 'success'});
  } else {
    mainStore.addNotification({content: 'An error has happened during the test suite execution', color: 'error'});
  }
  await loadData();
}
</script>
