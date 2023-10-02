<template>
  <v-card class='mb-4' id='resultCard' outlined>
    <v-card-title>LLM response</v-card-title>
    <v-card-text class='text-center card-text' v-if='inputData'>
      <LoadingFullscreen v-show='loading' name='result' class='pb-6' />
      <v-row v-if='prediction && !loading'>
        <v-col>
          <div class='mb-3 text-start generation-box'>
            <span class='generation-response'>{{ prediction }}</span>
          </div>
        </v-col>
      </v-row>
      <v-row>
        <v-col v-if='!prediction && !errorMsg && !loading'>
          <p>No data yet</p>
        </v-col>
        <v-col v-if='errorMsg'>
          <p class='error--text'>
            {{ errorMsg }}
          </p>
        </v-col>
      </v-row>
    </v-card-text>
    <v-card-actions>
      <v-btn :loading='loading' :disabled='!predictionOutdated' text @click='submitPrediction'>Run model</v-btn>
      <v-btn v-if='!predictionOutdated && !loading && model.featureNames?.length === 1' text @click='addToTestSuite'>Add
        to test suite
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup lang='ts'>
import {computed, onMounted, ref} from 'vue';
import LoadingFullscreen from '@/components/LoadingFullscreen.vue';
import {api} from '@/api';
import {ModelDTO} from '@/generated-sources';
import * as _ from 'lodash';
import {CanceledError} from 'axios';
import {$vfm} from "vue-final-modal";
import AddTestToSuite from "@/views/main/project/modals/AddTestToSuite.vue";
import {storeToRefs} from "pinia";
import {useCatalogStore} from "@/stores/catalog";

interface Props {
  projectId: number,
  model: ModelDTO;
  datasetId: string;
  modelFeatures: string[];
  inputData: { [key: string]: string };
  modified?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  modified: false
});

const {testFunctionsByUuid} = storeToRefs(useCatalogStore());

const prediction = ref<string | number | undefined>('');
const predictedInput = ref<{ [key: string]: string }>({});
const loading = ref<boolean>(false);
const errorMsg = ref<string>('');
const controller = ref<AbortController | undefined>(undefined);

async function submitPrediction() {
  if (controller.value) {
    controller.value.abort();
  }
  controller.value = new AbortController();
  if (Object.keys(props.inputData).length) {
    try {
      loading.value = true;
      predictedInput.value = _.pick(props.inputData, props.modelFeatures);
      const predictionResult = (await api.predict(
          props.model.id,
          props.datasetId,
          predictedInput.value,
          controller.value
      ));
      prediction.value = predictionResult.prediction;

      emit('result', prediction.value);

      errorMsg.value = '';
      loading.value = false;
    } catch (error) {
      if (!(error instanceof CanceledError)) {
        errorMsg.value = error.response.data.detail;
        prediction.value = undefined;
        loading.value = false;
      }
    }
  } else {
    // reset
    errorMsg.value = '';
    prediction.value = undefined;
  }
}

function addToTestSuite() {
  $vfm.show({
    component: AddTestToSuite,
    bind: {
      projectId: props.projectId,
      test: testFunctionsByUuid.value['1c6ec6db-8bdb-5446-a81e-4f0ceeb3a27e'],
      displayName: '{evaluation_criteria}',
      testArguments: {
        model: {
          name: 'model',
          value: props.model.id,
          type: 'Model',
          isAlias: false
        },
        prompt_input: {
          name: 'prompt_input',
          value: props.inputData[props.model.featureNames[0]],
          type: 'str',
          isAlias: false
        }
      },
      readOnlyInputs: ['model', 'prompt_input']
    }
  });
}

const predictionOutdated = computed(() => !_.isEqual(
    _.pick(props.inputData, props.modelFeatures),
    _.pick(predictedInput.value, props.modelFeatures)
));

const emit = defineEmits(['result']);

onMounted(async () => {
  await submitPrediction();
});
</script>

<style scoped>
.card-text {
  position: relative;
}

.v-data-table tbody td {
  font-size: 10px !important;
}

.generation-response {
  white-space: pre;
  text-wrap: wrap;
  font-family: 'Montserrat', "Helvetica Neue", sans-serif;
  color: black;
  font-size: 1rem;
}

.generation-box {
  border-radius: 5px 5px 5px 5px;
  -webkit-border-radius: 5px 5px 5px 5px;
  -moz-border-radius: 5px 5px 5px 5px;
  border: 1px solid #CCC;
  padding: 4px;
}

/** **/
</style>
