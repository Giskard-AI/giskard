<template>
  <div>
    <vue-final-modal v-slot="{ close }" classes="modal-container" content-class="modal-content" v-bind="$attrs" v-on="$listeners">
      <div v-if="isMLWorkerConnected" class="text-center">

        <v-card>
          <v-card-title>
            Configure run parameters
          </v-card-title>

          <v-card-text clas>
            <div class="d-flex flex-wrap">
              <div v-for="(input, idx) of testSuiteInputs" :class="{ 'border-execution': testSuiteInputs.length > 1 }">
                <div class="d-flex justify-end">
                  <v-btn v-if="idx > 1" color="error" icon @click="() => { testSuiteInputs.splice(idx, 1) }">
                    <v-icon>delete</v-icon>
                  </v-btn>
                </div>
                <div v-if="Object.entries(input.globalInput).length > 0">
                  <h4>Global inputs</h4>
                  <SuiteInputListSelector :inputs="globalTypes" :model-value="input.globalInput" :project-id="props.projectId" editing />
                </div>
                <div v-if="Object.entries(input.sharedInputs).length > 0">
                  <h4>Shared inputs</h4>
                  <SuiteInputListSelector :inputs="sharedTypes" :model-value="input.sharedInputs" :project-id="props.projectId" editing />
                </div>
              </div>
            </div>
            <v-btn v-if="testSuiteInputs.length > 1" @click="() => testSuiteInputs = [...testSuiteInputs, {
              globalInput: createInputs(globalInputs),
              sharedInputs: createInputs(sharedInputs),
            }]">
              <v-icon>add</v-icon>
              Add another comparison
            </v-btn>
          </v-card-text>

          <v-divider></v-divider>

          <v-card-actions>
            <v-spacer></v-spacer>
            <v-menu v-if="testSuiteInputs.length === 1" offset-y>
              <template v-slot:activator="{ on, attrs }">
                <v-btn :disabled="!isAllParamsSet()" :loading="running" color="primary" outlined v-bind="attrs">
                  <v-icon @click="executeTestSuite(close)">arrow_right</v-icon>
                  <span class="pe-2" @click="executeTestSuite(close)">Run test suite</span>
                  <v-icon class="ps-2 primary-left-border" v-on="on">mdi-menu-down</v-icon>
                </v-btn>
              </template>
              <v-list>
                <v-list-item>
                  <v-tooltip v-if="testSuiteInputs.length === 1 && !running" bottom>
                    <template v-slot:activator="{ on, attrs }">
                      <v-btn :disabled="!isAllParamsSet()" color="secondary" text v-bind="attrs" @click="tryTestSuite(close)" v-on="on">
                        <v-icon>science</v-icon>
                        Try test suite
                      </v-btn>
                    </template>
                    <span>Try out the test suite on a dataset sample.<br />The execution result won't be saved!</span>
                  </v-tooltip>
                </v-list-item>
              </v-list>
            </v-menu>
            <v-btn v-else :disabled="!isAllParamsSet()" :loading="running" color="primary" outlined>
              <v-icon @click="executeTestSuite(close)">arrow_right</v-icon>
              <span class="pe-2" @click="executeTestSuite(close)">Run test suite</span>
            </v-btn>
          </v-card-actions>
        </v-card>
      </div>
      <v-card v-else>
        <v-card-title class="py-6">
          <h2>ML Worker is not connected</h2>
        </v-card-title>
        <v-card-text>
          <StartWorkerInstructions></StartWorkerInstructions>
        </v-card-text>
      </v-card>
    </vue-final-modal>
  </div>
</template>

<script lang="ts" setup>

import { computed, onMounted, ref } from 'vue';
import mixpanel from 'mixpanel-browser';
import SuiteInputListSelector from '@/components/SuiteInputListSelector.vue';
import { useMainStore } from "@/stores/main";
import { useTestSuiteStore } from '@/stores/test-suite';
import { FunctionInputDTO, RequiredInputDTO } from '@/generated-sources';
import { useRouter } from 'vue-router/composables';
import { chain } from 'lodash';
import { TYPE } from "vue-toastification";
import { state } from "@/socket";
import StartWorkerInstructions from "@/components/StartWorkerInstructions.vue";

const props = defineProps<{
  projectId: number,
  suiteId: number,
  inputs: { [name: string]: RequiredInputDTO },
  compareMode: boolean,
  previousParams: { [name: string]: string }
}>();

const mainStore = useMainStore();
const testSuiteStore = useTestSuiteStore();

const running = ref<boolean>(false);

const testSuiteInputs = ref<{
  globalInput: {
    [name: string]: FunctionInputDTO
  },
  sharedInputs: {
    [name: string]: FunctionInputDTO
  }
}[]>([]);

const isMLWorkerConnected = computed(() => {
  return state.workerStatus.connected;
});

const inputs = computed(() => Object.keys(props.inputs).map((name) => ({
  ...props.inputs[name],
  name,
})));

const globalInputs = computed(() => inputs.value.filter(i => !i.sharedInput))
const sharedInputs = computed(() => inputs.value.filter(i => i.sharedInput))

const globalTypes = computed(() => chain(globalInputs.value)
  .keyBy('name')
  .mapValues('type')
  .value())

const sharedTypes = computed(() => chain(sharedInputs.value)
  .keyBy('name')
  .mapValues('type')
  .value())

function createInputs(inputs: (RequiredInputDTO & { name: string })[]) {
  return inputs
    .reduce((result, { name, type }) => {
      result[name] = {
        isAlias: false,
        name,
        type,
        value: testSuiteStore.suite!.functionInputs.find(t => t.name === name)?.value ?? props.previousParams[name] ?? ''
      }
      return result;
    }, {});
}

onMounted(async () => {
  testSuiteInputs.value = props.compareMode ? [{
    globalInput: createInputs(globalInputs.value),
    sharedInputs: createInputs(sharedInputs.value),
  }, {
    globalInput: createInputs(globalInputs.value),
    sharedInputs: createInputs(sharedInputs.value),
  }] : [{
    globalInput: createInputs(globalInputs.value),
    sharedInputs: createInputs(sharedInputs.value),
  }];
})

function isAllParamsSet() {
  return testSuiteInputs.value
    .filter(({ sharedInputs, globalInput }) => Object.entries(props.inputs)
      .map(([name, { sharedInput }]) => sharedInput ? sharedInputs[name] : globalInput[name])
      .findIndex(param => param && (param.value === null || param.value!.trim() === '')) !== -1)
    .length === 0;
}

const router = useRouter();

async function executeTestSuite(close) {
  running.value = true;

  try {
    const jobUuids = await Promise.all(testSuiteInputs.value.map(input =>
      testSuiteStore.runTestSuite([
        ...Object.values(input.globalInput),
        ...Object.values(input.sharedInputs)
      ])
    ));

    if (props.compareMode) {
      await Promise.all(jobUuids.map(({ trackJob }) => trackJob));
      await router.push({ name: 'project-testing-test-suite-compare-executions', query: { latestCount: jobUuids.length.toString() } })
    } else {
      mainStore.addNotification({ content: 'Test suite execution has been scheduled', color: TYPE.SUCCESS });
    }
    // Track job asynchronously
  } finally {
    running.value = false;
    close();
  }
}

async function tryTestSuite(close) {
  mixpanel.track('Try test suite', { suiteId: props.suiteId });
  running.value = true;

  try {
    const input = testSuiteInputs.value[0];
    await testSuiteStore.tryTestSuite([
      ...Object.values(input.globalInput),
      ...Object.values(input.sharedInputs)
    ]);
  } finally {
    running.value = false;
    close();
    await router.push({ name: 'project-testing-test-suite-overview' })
  }
}
</script>

<style scoped>
::v-deep(.modal-container) {
  display: flex;
  justify-content: center;
  align-items: center;
}

::v-deep(.modal-content) {
  position: relative;
  display: flex;
  flex-direction: column;
  margin: 0 1rem;
  padding: 1rem;
  min-width: 50vw;
}

.border-execution {
  border-radius: 10px;
  -webkit-border-radius: 10px;
  -moz-border-radius: 10px;
  border: 1px solid #000000;
  margin: 8px;
  padding: 4px;
}

.primary-left-border {
  border-left: 1px solid #087038;
}
</style>
