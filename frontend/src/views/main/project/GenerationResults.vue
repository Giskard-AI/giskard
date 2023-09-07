<template>
  <v-card class='mb-4' id='resultCard' outlined>
    <v-card-title>Result</v-card-title>
    <v-card-text class='text-center card-text' v-if='inputData'>
      <LoadingFullscreen v-show='loading' name='result' class='pb-6' />
      <v-row v-if='prediction && !loading'>
        <v-col>
          <div class='mb-3 text-start'>
            <span class='whitespace-pre'>{{ prediction }}</span>
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
      <v-btn :loading='loading' :disabled='!predictionOutdated' text @click='submitPrediction'>Generate</v-btn>
      <v-btn v-if='!predictionOutdated && !loading && modified' text @click='saveInput'>Save</v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup lang='ts'>
import { computed, onMounted, ref } from 'vue';
import LoadingFullscreen from '@/components/LoadingFullscreen.vue';
import { api } from '@/api';
import { ModelDTO } from '@/generated-sources';
import * as _ from 'lodash';
import { CanceledError } from 'axios';
import { openapi } from '@/api-v2';

interface Props {
  model: ModelDTO;
  datasetId: string;
  modelFeatures: string[];
  inputData: { [key: string]: string };
  modified?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  modified: false
});

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

function saveInput() {
  openapi.datasets.addRow({
    projectKey: props.model.project.key,
    datasetId: props.datasetId,
    requestBody: props.inputData
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

.whitespace-pre {
  white-space: pre;
}

/** **/
</style>
