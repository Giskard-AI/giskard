<template>
  <div>
    <vue-final-modal
        v-slot="{ close }"
        v-bind="$attrs"
        classes="modal-container"
        content-class="modal-content"
        v-on="$listeners"
    >
      <div class="text-center">

        <v-card>
          <v-card-title>
            Configure run parameters
          </v-card-title>

          <v-card-text clas>
            <div class="d-flex flex-wrap">
              <div v-for="(input, idx) of testSuiteInputs"
                   :class="{'border-execution': testSuiteInputs.length > 1}">
                <div class="d-flex justify-end">
                  <v-btn icon v-if="idx > 1"
                         @click="() => {testSuiteInputs.splice(idx, 1)}"
                         color="error">
                    <v-icon>delete</v-icon>
                  </v-btn>
                </div>
                <div v-if="Object.entries(input.globalInput).length > 0">
                  <h4>Global inputs</h4>
                  <SuiteInputListSelector
                      editing
                      :model-value="input.globalInput"
                      :inputs="globalTypes"
                      :project-id="props.projectId"
                  />
                </div>
                <div v-if="Object.entries(input.sharedInputs).length > 0">
                  <h4>Shared inputs</h4>
                  <SuiteInputListSelector
                      editing
                      :model-value="input.sharedInputs"
                      :inputs="sharedTypes"
                      :project-id="props.projectId"
                  />
                </div>
              </div>
            </div>
            <v-btn v-if="testSuiteInputs.length > 1"
                   @click="() => testSuiteInputs = [...testSuiteInputs, {
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
            <v-btn
                color="primary"
                text
                @click="executeTest(close)"
                :disabled="!isAllParamsSet() || running"
            >
              <v-icon>arrow_right</v-icon>
              <template v-if="debug">Debug test</template>
              <template v-else>Run test</template>
            </v-btn>
          </v-card-actions>
        </v-card>
      </div>
    </vue-final-modal>
  </div>
</template>

<script setup lang="ts">

import {computed, onMounted, ref} from 'vue';
import SuiteInputListSelector from '@/components/SuiteInputListSelector.vue';
import {useMainStore} from "@/stores/main";
import {useTestSuiteStore} from '@/stores/test-suite';
import {FunctionInputDTO, RequiredInputDTO} from '@/generated-sources';
import {useRouter} from 'vue-router/composables';
import {chain} from 'lodash';
import {api} from "@/api";

const props = defineProps<{
  projectId: number,
  suiteId: number,
  testUuid: string,
  inputs: { [name: string]: RequiredInputDTO },
  compareMode: boolean,
  previousParams: { [name: string]: string },
  debug: false
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
      .reduce((result, {name, type}) => {
        result[name] = {
          isAlias: false,
          name,
          type,
          value: testSuiteStore.suite!.functionInputs.find(t => t.name === name)?.value ?? props.previousParams[name] ?? ''
        }
        return result;
      }, {});
}

onMounted(() => {
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
      .filter(({sharedInputs, globalInput}) => Object.entries(props.inputs)
          .map(([name, {sharedInput}]) => sharedInput ? sharedInputs[name] : globalInput[name])
          .findIndex(param => param && (param.value === null || param.value!.trim() === '')) !== -1)
      .length === 0;
}

const router = useRouter();

async function executeTest(close) {
  //mixpanel.track('Run test', {suiteId: props.suiteId});
  let input = testSuiteInputs.value[0];
  debugger;
  await api.runAdHocTest(props.projectId, props.testUuid, [
    ...Object.values(input.globalInput),
    ...Object.values(input.sharedInputs)
  ]);

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

</style>
