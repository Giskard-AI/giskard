<template>
  <div class="vc">
    <div class="vc">
      <v-container class="main-container vc">
        <v-row class="fill-height">
          <v-col cols="4" class="vc fill-height">
            <v-list three-line v-if="testFunctions">
              <v-list-item-group v-model="selected" color="primary" mandatory>
                <template v-for="(test, index) in testFunctions">
                  <v-divider/>
                  <v-list-item :value="test">
                    <v-list-item-content>
                      <v-list-item-title v-text="test.name" class="test-title"></v-list-item-title>

                      <v-list-item-subtitle v-if="test.tags">
                        <v-chip class="mr-2" v-for="tag in sorted(test.tags)" x-small :color="pasterColor(tag)">
                          {{ tag }}
                        </v-chip>
                      </v-list-item-subtitle>
                    </v-list-item-content>

                  </v-list-item>
                </template>
              </v-list-item-group>
            </v-list>
          </v-col>
          <v-col cols="8" v-if="selected" class="vc fill-height">
            <div class="d-flex justify-space-between">
              <span class="text-h5">{{ selected.name }}</span>
              <v-btn small outlined tile class="primary" color="white">
                <v-icon dense class="pr-2">mdi-plus</v-icon>
                Add to test suite
              </v-btn>
            </div>
<!--            <AddTestToTestSuiteModal style="border: 1px solid lightgrey"></AddTestToTestSuiteModal>-->
            <div class="vc overflow-x-hidden pr-5">

              <pre class="test-doc caption pt-5">{{ selected.doc }}</pre>
              <div class="pt-5">
                <div class="d-flex justify-space-between">
                  <span class="text-h6">Inputs</span>
                  <v-btn width="100" small tile outlined @click="tryMode = !tryMode">{{
                      tryMode ? 'Cancel' : 'Try it'
                    }}
                  </v-btn>
                </div>
                <v-list>
                  <v-list-item v-for="a in selected.arguments" class="pl-0 pr-0">
                    <v-row>
                      <v-col>
                        <v-list-item-content>
                          <v-list-item-title>{{ a.name }}</v-list-item-title>
                          <v-list-item-subtitle class="text-caption">{{ a.type }}</v-list-item-subtitle>
                          <v-list-item-action-text v-show="!!a.optional">Optional. Default: <code>{{
                              a.default
                            }}</code>
                          </v-list-item-action-text>
                        </v-list-item-content>
                      </v-col>
                      <v-col>
                        <template v-if="tryMode">
                          <DatasetSelector :project-id="projectId" :label="a.name" :return-object="false"
                                           v-if="a.type === 'GiskardDataset'" :value.sync="testArguments[a.name]"/>
                          <ModelSelector :project-id="projectId" :label="a.name" :return-object="false"
                                         v-if="a.type === 'GiskardModel'" :value.sync="testArguments[a.name]"/>
                          <v-text-field
                              :step='a.type === "float" ? 0.1 : 1'
                              v-model="testArguments[a.name]"
                              v-if="['float', 'int'].includes(a.type)"
                              hide-details
                              single-line
                              type="number"
                              outlined
                              dense
                          />
                        </template>
                      </v-col>
                    </v-row>
                  </v-list-item>
                </v-list>
                <v-row v-show="tryMode">
                  <v-col :align="'right'">
                    <v-btn width="100" small tile outlined class="primary" color="white" @click="runTest">Run
                    </v-btn>
                  </v-col>
                </v-row>
                <v-row style="height: 150px">
                  <v-col v-if="testResult">
                    <TestExecutionResultBadge :result="testResult"/>
                  </v-col>
                </v-row>
              </div>
            </div>

          </v-col>
        </v-row>
      </v-container>
    </div>
  </div>
</template>

<script setup lang="ts">
import {api} from "@/api";
import _ from "lodash";
import {computed, onActivated, ref, watch} from "vue";
import {pasterColor} from "@/utils";
import ModelSelector from "@/views/main/utils/ModelSelector.vue";
import DatasetSelector from "@/views/main/utils/DatasetSelector.vue";
import TestExecutionResultBadge from "@/views/main/project/TestExecutionResultBadge.vue";
import AddTestToTestSuiteModal from "@/views/main/project/AddTestToTestSuiteModal.vue"

defineProps<{
  projectId: number
}>()

let registry = ref(null);
let selected = ref(null);
let tryMode = ref(true)
let testArguments = ref({})
let testResult = ref(null);

let openFeedbackDetail = false

async function runTest() {
  testResult.value = await api.runAdHocTest(selected.value.id, testArguments.value);
}


function castDefaultValueToType(arg) {
  switch (arg.type) {
    case 'float':
      return parseFloat(arg.default)
    case 'int':
      return parseInt(arg.default)
    default:
      return arg.default;
  }
}

watch(selected, (value) => {
  testResult.value = null;
  tryMode.value = false;
  testArguments.value = {}
  for (const [argName, arg] of Object.entries(value.arguments)) {
    testArguments.value[argName] = castDefaultValueToType(arg);
  }
});


function sorted(arr: any[]) {
  const res = _.cloneDeep(arr);
  res.sort()
  return res;
}

const testFunctions = computed(() => {
  // @ts-ignore
  return _.sortBy(registry.value?.functions, 'name');
})

onActivated(async () => {
  registry.value = await api.getTestsRegistry();
  if (testFunctions) {
    selected.value = testFunctions[0];
  }
});

</script>

<style scoped lang="scss">
.main-container {
  width: 100%;
  max-width: 100%;
}

.test-title {
  white-space: break-spaces;
}

.box-grow {
  flex: 1; /* formerly flex: 1 0 auto; */
  background: green;
  padding: 5px;
  margin: 5px;
  min-height: 0; /* new */
}

.test-doc {
  white-space: break-spaces;
}


</style>
