<template>
  <v-container fluid class="vc">
    <v-row>
      <v-col :align="'right'">
        <RunTestSuiteModal :inputs="inputs" :suite-id="suiteId" :project-id="projectId"/>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="2">
        <v-tabs vertical v-model="tab">
          <v-tab>Inputs & parameters</v-tab>
          <v-tab>Tests</v-tab>
          <v-tab>Configuration</v-tab>
          <v-tab>Execution</v-tab>
        </v-tabs>
      </v-col>
      <v-col>
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
                        :test="registry.tests[selectedTest.testId]"
                        :models="allModels"
                        :datasets="allDatasets"
                        :inputs="selectedTest.testInputs"/>
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
                                 :inputTypes="inputs"/>
          </v-tab-item>
        </v-tabs-items>
      </v-col>
    </v-row>
  </v-container>
</template>

<script lang="ts" setup>

import {api} from "@/api";
import {onMounted, ref} from "vue";
import {DatasetDTO, ModelDTO, SuiteTestDTO, TestCatalogDTO, TestSuiteNewDTO} from "@/generated-sources";
import TestSuiteTestDetails from "@/views/main/project/TestSuiteTestDetails.vue";
import RunTestSuiteModal from '@/views/main/project/modals/RunTestSuiteModal.vue';
import TestSuiteExecutions from '@/views/main/project/TestSuiteExecutions.vue';

const props = defineProps<{
  projectId: number,
  suiteId: number,
}>();

let suite = ref<TestSuiteNewDTO | null>(null);
let registry = ref<TestCatalogDTO | null>(null);
let tab = ref<any>(null);
let selectedTest = ref<SuiteTestDTO | null>(null);
let inputs = ref<{
  [name: string]: string
}>({});
const allDatasets = ref<{ [key: string]: DatasetDTO }>({});
const allModels = ref<{ [key: string]: ModelDTO }>({});

onMounted(async () => {
  // Call api in parallel to shorten loading time
  const [
    inputResults,
    suiteResults,
    registryResult,
    datasets,
    models
  ] = await Promise.all([
    api.getTestSuiteNewInputs(props.projectId, props.suiteId),
    api.getTestSuiteNew(props.projectId, props.suiteId),
    api.getTestsCatalog(props.projectId),
    api.getProjectDatasets(props.projectId),
    api.getProjectModels(props.projectId)
  ]);

  inputs.value = inputResults;
  suite.value = suiteResults;
  registry.value = registryResult

  allDatasets.value = Object.fromEntries(datasets.map(x => [x.id, x]));
  allModels.value = Object.fromEntries(models.map(x => [x.id, x]));
})

</script>
