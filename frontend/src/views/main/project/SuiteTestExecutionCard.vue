<template>
  <div class='test-container'>
    <div class='d-flex flex-row flex-wrap align-center test-card-header'>
      <span class='test-name text-black'>
          Test {{ suiteTest.test.displayName ?? suiteTest.test.name }}
          <span v-if='transformationFunction'> to {{
              transformationFunction.displayName ?? transformationFunction.name
            }}</span>
                <span v-if='slicingFunction'> on slice {{ slicingFunction.displayName ?? slicingFunction.name }}</span>
            </span>
      <!-- TODO: Add tag to the test suite level (https://github.com/Giskard-AI/giskard/issues/1034)
          <div class="d-flex flex-row gap-4">
              <v-chip v-if="!compact" v-for="tag in sorted(suiteTest.test.tags)" x-small :color="pasterColor(tag)"
                      label>
                  {{ tag }}
              </v-chip>
          </div>
      -->
      <div class='flex-grow-1'/>
      <div v-if='result' :class='`d-flex flex-row flex-wrap align-center gap-8 test-${result.status.toLowerCase()}`'>
                <span v-if='result.metric' class='metric'>Measured <strong>Metric = {{
                    result.metric
                  }}</strong></span>
        <v-chip :color='TEST_RESULT_DATA[result.status].color'
                :text-color='TEST_RESULT_DATA[result.status].textColor'
                label link @click='openLogs'>
          <v-icon class='mr-1'>{{ TEST_RESULT_DATA[result.status].icon }}</v-icon>
          {{ TEST_RESULT_DATA[result.status].capitalized }}
        </v-chip>
        <v-btn color='primary' @click='debugTest' outlined small :disabled='!canBeDebugged' :loading='loading'>
          <v-icon small>info</v-icon>
          Debug
        </v-btn>
      </div>
    </div>
    <div class='d-flex flex-row flex-wrap align-end test-card-footer'>
      <div v-for='({ name, value, type }) in orderedParams' class='d-flex flex-column'>
        <span class='text-input-name'>{{ name }}</span>
        <span :class="['BaseModel', 'Dataset'].includes(type) ? 'text-input-value' : 'text-input-value-code'">{{
            value
          }}</span>
      </div>
      <div class='flex-grow-1'/>
      <v-btn v-if='!isPastExecution' color='rgba(0, 0, 0, 0.6)' small text @click='editTests'>
        <v-icon class='mr-1' small>settings</v-icon>
        Edit parameters
      </v-btn>
    </div>

    <div>
      <v-dialog
          v-model="modelDialog"
          width="auto"
      >
        <v-card>
          <v-card-text>
            <v-card-title>
              Select a model to debug with
            </v-card-title>
            <ModelSelector
                :project-id="testSuiteStore.projectId"
                label="Model"
                :return-object="false"
                @update:value="onSelectModel"
                :value.sync="selectedModel"/>
          </v-card-text>
        </v-card>
      </v-dialog>
    </div>
    <div>
      <v-dialog
          v-model="loading"
          width="auto"
      >
        <v-card>
          <v-card-title>Loading debug session</v-card-title>
          <v-card-text>
            <v-progress-linear indeterminate></v-progress-linear>
          </v-card-text>
        </v-card>
      </v-dialog>
    </div>
  </div>
</template>

<script lang='ts' setup>
import {SuiteTestDTO, SuiteTestExecutionDTO} from '@/generated-sources';
import {computed, ref} from 'vue';
import {storeToRefs} from 'pinia';
import {useCatalogStore} from '@/stores/catalog';
import {$vfm} from 'vue-final-modal';
import SuiteTestInfoModal from '@/views/main/project/modals/SuiteTestInfoModal.vue';
import {useTestSuiteStore} from '@/stores/test-suite';
import {useDebuggingSessionsStore} from '@/stores/debugging-sessions';
import ExecutionLogsModal from '@/views/main/project/modals/ExecutionLogsModal.vue';
import mixpanel from 'mixpanel-browser';
import {TEST_RESULT_DATA} from '@/utils/tests.utils';
import {api} from '@/api';
import router from '@/router';
import ModelSelector from '@/views/main/utils/ModelSelector.vue';
import {chain} from 'lodash';
import {$tags} from "@/utils/nametags.utils";

const {slicingFunctionsByUuid, transformationFunctionsByUuid} = storeToRefs(useCatalogStore());
const {models, datasets} = storeToRefs(useTestSuiteStore());

const testSuiteStore = useTestSuiteStore();
const debuggingSessionStore = useDebuggingSessionsStore();

const props = defineProps<{
  suiteTest: SuiteTestDTO,
  result?: SuiteTestExecutionDTO,
  compact: boolean,
  isPastExecution: boolean
}>();

const loading = ref<boolean>(false);
const modelDialog = ref<boolean>(false);
const selectedModel = ref<string>("");

const params = computed(() => props.isPastExecution && props.result
    ? props.result?.inputs
    : Object.values(props.suiteTest.functionInputs)
        .filter(input => !input.isAlias)
        .reduce((r, input) => ({...r, [input.name]: input.value}), {}));

function mapValue(value: string, type: string): string {
  if (type === 'SlicingFunction') {
    const slicingFunction = slicingFunctionsByUuid.value[value];
    return slicingFunction?.displayName ?? slicingFunction?.name ?? value;
  } else if (type === 'TransformationFunction') {
    const transformationFunction = transformationFunctionsByUuid.value[value];
    return transformationFunction?.displayName ?? transformationFunction?.name ?? value;
  } else if (type === 'BaseModel') {
    const model = models.value[value];
    return model.name ?? value;
  } else if (type === 'Dataset') {
    const dataset = datasets.value[value];
    return $tags(dataset.name) ?? value;
  }
  return value;
}

const orderedParams = computed(() => params.value ? props.suiteTest.test.args
        .filter(({name}) => params.value!.hasOwnProperty(name))
        .map(({name, type}) => ({
          name: name.split('_').map(word => word[0].toUpperCase() + word.slice(1)).join(' '),
          value: mapValue(params.value[name], type),
          type
        }))
    : []);

const slicingFunction = computed(() => {
  const uuid = params.value ? params.value['slicing_function'] : undefined;

  if (uuid) {
    return slicingFunctionsByUuid.value[uuid];
  } else {
    return undefined;
  }
});

const transformationFunction = computed(() => {
  const uuid = params.value ? params.value['transformation_function'] : undefined;

  if (uuid) {
    return transformationFunctionsByUuid.value[uuid];
  } else {
    return undefined;
  }
});

const errors = computed(() => props.result?.messages?.filter(message => message.type === 'ERROR') ?? []);

async function onSelectModel(modelUuid) {
  await runDebug(undefined, modelUuid);
}

async function editTests() {
  await $vfm.show({
    component: SuiteTestInfoModal,
    bind: {
      suiteTest: props.suiteTest
    }
  });
}

async function debugTest() {
  let inputs = createDebugInputs();
  let models = inputs.filter(i => i.name == "model");
  if (models.length == 0) {
    modelDialog.value = true;
    return;
  }

  let model = models[0].value;
  await runDebug(inputs, model);
}

async function runDebug(inputs, modelId: string) {
  if (inputs == undefined) {
    inputs = createDebugInputs();
  }

  try {
    modelDialog.value = false;
    loading.value = true;
    let res = await api.runAdHocTest(testSuiteStore.projectId!, props.suiteTest.testUuid, inputs, false, true);
    let dataset = res.result[0].result.outputDfUuid;

    const debuggingSession = await api.prepareInspection({
      datasetId: dataset,
      modelId: modelId,
      name: "Debugging session for " + props.suiteTest.test.name,
      sample: true
    });
    debuggingSessionStore.setCurrentDebuggingSessionId(debuggingSession.id);

    await router.push({
      name: 'project-debugger',
    })
  } finally {
    loading.value = false;
    selectedModel.value = "";
  }
}

function createDebugInputs() {
  let inputs: any[] = []; // FunctionInputDTO, ideally
  function parseArguments(res, args) {
    Object.keys(args).forEach(key => {
      var parsed = JSON.parse(args[key]);
      //let arg = args[key];
      var params = [];
      if (parsed.args != undefined) {
        parseArguments(params, parsed.args);
      }

      res.push({
        name: key,
        isAlias: false,
        value: parsed.value,
        params: params
      })
    })
  }

  parseArguments(inputs, props.result?.arguments);

  let base_result = chain(props.suiteTest?.functionInputs)
      .keyBy('name')
      .mapValues(arg => ({
        name: arg.name,
        isAlias: false,
        type: arg.type,
        value: arg.value,
        params: arg.params
      }))
      .value();

  // Here we merge base_input and inputs
  for (let i = 0; i < inputs.length; i++) {
    let input = inputs[i];
    // if field exists in base_result
    if (base_result[input.name] != undefined) {
      // set its value = to inputs' value
      base_result[input.name].value = input.value;
    } else {
      // else add it as-is
      base_result[input.name] = input;
    }
  }

  // transform base_result into an array instead of a map, ditching the keys
  inputs = Object.keys(base_result).map(key => base_result[key]);

  return inputs;
}

function openLogs() {
  $vfm.show({
    component: ExecutionLogsModal,
    bind: {
      logs: errors.value.map(({text}) => text).join('\n')
    }
  });

  mixpanel.track('Open test error logs');
}

const canBeDebugged = computed(() => {
  return !(props.result?.status == "PASSED") && props.suiteTest.test.args.filter(arg => arg.name === 'debug' && arg.type === 'bool').length > 0;
});
</script>

<style lang='scss' scoped>
.test-container {
  border-radius: 4px 4px 4px 4px;
  -webkit-border-radius: 4px 4px 4px 4px;
  -moz-border-radius: 4px 4px 4px 4px;
  border: 1px solid rgb(224, 224, 224);
  background: white;
}

.test-card-header {
  padding: 10px;
  gap: 20px;
}

.test-card-footer {
  border-top: 1px solid #dee2e6;
  padding: 10px;
  gap: 20px;
}


.test-name {
  font-style: normal;
  font-weight: 500;
  font-size: 1em;
  line-height: 20px;
  letter-spacing: 0.0025em;
  color: #000000;
}

.gap-4 {
  gap: 8px;
}

.gap-8 {
  gap: 8px;
}

.metric {
  font-style: normal;
  font-weight: 400;
  font-size: 0.875em;
  line-height: 16px;
  letter-spacing: 0.0025em;
}

.test-failed {
  .metric {
    color: #B71C1C;
  }
}

.text-input-name {
  font-style: normal;
  font-weight: 400;
  font-size: 0.875em;
  line-height: 12px;
  letter-spacing: 0.0025em;
}

.text-input-value {
  font-style: normal;
  font-weight: 400;
  font-size: 0.875em;
  line-height: 24px;
  font-feature-settings: 'liga' off;
  color: #000000;
}

.text-input-value-code {
  font-family: 'Fira Code', "Helvetica Neue", sans-serif;
  font-style: normal;
  font-weight: 400;
  font-size: 0.75em;
  line-height: 24px;
  font-feature-settings: 'liga' off;
  color: #000000;
}
</style>

