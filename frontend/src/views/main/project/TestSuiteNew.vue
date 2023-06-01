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
          <v-tab>Inputs & parameters</v-tab>
          <v-tab>Tests</v-tab>
          <v-tab>Configuration</v-tab>
          <v-tab>Execution</v-tab>
          <v-tab class="d-none">Compare executions</v-tab>
          <v-tab class="d-none">Compare tests</v-tab>
        </v-tabs>
      </v-col>
      <v-col cols="10">
        <v-tabs-items v-model="tab">
          <v-tab-item :transition="false">
            <div>Inputs</div>
            <v-list>
              <v-list-item v-for="(type, name) in inputs">
                <v-list-item-title>{{ name }}: {{ type }}</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-tab-item>
          <v-tab-item :transition="false">
            <v-row v-if="registry">
              <v-col cols="3">
                <v-list three-line v-if="suite.tests">
                  <v-list-item-group v-model="selectedTest" color="primary" mandatory>
                    <template v-for="(test) in suite.tests">
                      <v-divider/>
                      <v-list-item :value="test">
                        <v-list-item-content>
                          <v-list-item-title v-text="registry.tests[test.testId].name"
                                             class="test-title"></v-list-item-title>
                        </v-list-item-content>
                      </v-list-item>
                    </template>
                  </v-list-item-group>
                </v-list>
              </v-col>
              <v-col v-if="selectedTest">
                <v-row>
                  <v-col>
                    <TestSuiteTestDetails
                        :project-id="projectId"
                        :suite-id="suiteId"
                        :test="registry.tests[selectedTest.testId]"
                        :models="allModels"
                        :datasets="allDatasets"
                        :inputs="selectedTest.testInputs"
                        :executions="testSuiteResults[selectedTest.testId]"
                        @updateTestSuite="loadData" />
                  </v-col>
                </v-row>
              </v-col>
            </v-row>
          </v-tab-item>
          <v-tab-item :transition="false">

          </v-tab-item>
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

import {api} from "@/api";
import {computed, onMounted, ref, watch} from "vue";
import {
  DatasetDTO,
  ModelDTO,
  SuiteTestDTO,
  TestCatalogDTO,
  TestSuiteExecutionDTO,
  TestSuiteNewDTO
} from "@/generated-sources";
import TestSuiteTestDetails from "@/views/main/project/TestSuiteTestDetails.vue";
import RunTestSuiteModal from '@/views/main/project/modals/RunTestSuiteModal.vue';
import TestSuiteExecutions from '@/views/main/project/TestSuiteExecutions.vue';
import {ArrayReducers} from '@/utils/array-reducers';
import useRouterTabsSynchronization from '@/utils/use-router-tabs-synchronization';
import TestSuiteCompareExecutions from '@/views/main/project/TestSuiteCompareExecutions.vue';
import TestSuiteCompareTest from '@/views/main/project/TestSuiteCompareTest.vue';
import {commitAddNotification} from '@/store/main/mutations';
import store from '@/store';
import {useTrackJob} from '@/utils/use-track-job';

const props = defineProps<{
  projectId: number,
  suiteId: number
}>();

const suite = ref<TestSuiteNewDTO | null>(null);
const registry = ref<TestCatalogDTO | null>(null);
const tab = ref<any>(null);
const selectedTest = ref<SuiteTestDTO | null>(null);
const inputs = ref<{ [name: string]: string }>({});
const allDatasets = ref<{ [key: string]: DatasetDTO }>({});
const allModels = ref<{ [key: string]: ModelDTO }>({});
const executions = ref<TestSuiteExecutionDTO[]>();

onMounted(() => loadData());

async function loadData() {
  // Call api in parallel to shorten loading time
  const [
    inputResults,
    suiteResults,
    registryResult,
    datasets,
    models,
    executionResults
  ] = await Promise.all([
    api.getTestSuiteNewInputs(props.projectId, props.suiteId),
    api.getTestSuiteNew(props.projectId, props.suiteId),
    api.getTestsCatalog(props.projectId),
    api.getProjectDatasets(props.projectId),
    api.getProjectModels(props.projectId),
    api.listTestSuiteExecutions(props.projectId, props.suiteId)
  ]);

  inputs.value = inputResults;
  suite.value = suiteResults;
  registry.value = registryResult
  executions.value = executionResults;

  allDatasets.value = Object.fromEntries(datasets.map(x => [x.id, x]));
  allModels.value = Object.fromEntries(models.map(x => [x.id, x]));

}

watch(() => suite.value, () => {
  if (selectedTest.value !== null && suite.value !== null) {
    selectedTest.value = suite.value.tests.find(test => test.testId === selectedTest.value?.testId) ?? null;
  }
})

const testSuiteResults = computed(() => {
  if (!executions.value) {
    return {};
  }

  return executions.value
      .map(execution => (execution.results ?? []).map(
          result => ({
            testResult: result,
            testSuiteResult: execution
          })
      ))
      .reduce((flattened, results) => flattened.concat(results), [])
      .reduce(ArrayReducers.groupBy(result => result.testResult.test.testId), {})
});

useRouterTabsSynchronization([
  'test-suite-new-inputs',
  'test-suite-new-test',
  'test-suite-new-configuration',
  'test-suite-new-execution',
  'test-suite-new-compare-executions',
  'test-suite-new-compare-test'
], tab);

const {
  trackedJobs,
  addJob
} = useTrackJob();
async function onExecutionScheduled(jobUuid: string) {
  const result = await addJob(jobUuid);
  if (result) {
    commitAddNotification(store, {content: 'Test suite execution has been executed successfully', color: 'success'});
  } else {
    commitAddNotification(store, {content: 'An error has happened during the test suite execution', color: 'error'});
  }
  await loadData();
}
</script>
