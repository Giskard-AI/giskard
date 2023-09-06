<template>
  <v-card class='mb-4' id='resultCard' outlined>
    <v-card-title>Result</v-card-title>
    <v-card-text class='text-center card-text' v-if='inputData'>
      <LoadingFullscreen v-show='loading' name='result' class='pb-6' />
      <v-row v-if='prediction && !loading'>
        <v-col>
          <div class='mb-3 text-start'>
            <span>{{ prediction }}</span>
          </div>
        </v-col>
      </v-row>
      <v-row>
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

  </v-card>
</template>

<script setup lang='ts'>
import { onMounted, ref } from 'vue';
import LoadingFullscreen from '@/components/LoadingFullscreen.vue';
import { api } from '@/api';
import { ModelDTO } from '@/generated-sources';
import * as _ from 'lodash';
import { CanceledError } from 'axios';

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
const resultProbabilities = ref<any>({});
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
      const predictionResult = (await api.predict(
          props.model.id,
          props.datasetId,
          _.pick(props.inputData, props.modelFeatures),
          controller.value
      ));
      prediction.value = predictionResult.prediction;
      emit('result', prediction.value);

      resultProbabilities.value = Object.entries(predictionResult.probabilities)
          .sort(([, v1], [, v2]) => +v2 - +v1)       // Sort the object by value - solution based on:
          .reduce((r, [k, v]) => ({ ...r, [k]: v }), {}); // https://stackoverflow.com/questions/55319092/sort-a-javascript-object-by-key-or-value-es6

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
    resultProbabilities.value = {};
  }
}

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
</style>
