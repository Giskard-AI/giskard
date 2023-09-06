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

    <v-card-actions v-show='Object.keys(resultProbabilities).length > predCategoriesN'>
      <ResultPopover :resultProbabilities='resultProbabilities' :prediction='prediction' :actual='actual'
                     :classColorPrediction='classColorPrediction'></ResultPopover>
    </v-card-actions>

  </v-card>
</template>

<script setup lang='ts'>
import { computed, getCurrentInstance, onMounted, ref, watch } from 'vue';
import ResultPopover from '@/components/ResultPopover.vue';
import LoadingFullscreen from '@/components/LoadingFullscreen.vue';
import { api } from '@/api';
import { use } from 'echarts/core';
import { BarChart } from 'echarts/charts';
import { CanvasRenderer } from 'echarts/renderers';
import { GridComponent } from 'echarts/components';
import { ModelDTO, ModelType } from '@/generated-sources';
import * as _ from 'lodash';
import { CanceledError } from 'axios';

use([CanvasRenderer, BarChart, GridComponent]);

const instance = getCurrentInstance();

interface Props {
  model: ModelDTO;
  datasetId: string;
  predictionTask: ModelType;
  targetFeature: string;
  modelFeatures: string[];
  classificationLabels: string[];
  inputData: { [key: string]: string };
  modified?: boolean;
  debounceTime?: number;
}

const props = withDefaults(defineProps<Props>(), {
  modified: false,
  debounceTime: 250
});

const prediction = ref<string | number | undefined>('');
const resultProbabilities = ref<any>({});
const loading = ref<boolean>(false);
const errorMsg = ref<string>('');
const predCategoriesN = ref<number>(5);
const controller = ref<AbortController | undefined>(undefined);

const actual = computed(() => {
  if (props.targetFeature && !errorMsg.value) return props.inputData[props.targetFeature];
  else return undefined;
});

const isCorrectPrediction = computed(() => {
  if (_.isNumber(actual.value) || _.isNumber(prediction.value)) {
    return _.toNumber(actual.value) === _.toNumber(prediction.value);
  } else {
    return _.toString(actual.value) === _.toString(prediction.value);
  }
});

const classColorPrediction = computed(() => {
  if (actual.value === null) return 'info--text text--darken-2';
  else return isCorrectPrediction.value ? 'primary--text' : 'error--text';
});

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

const debouncedSubmitPrediction = _.debounce(async () => {
  await submitPrediction();
}, props.debounceTime);

const emit = defineEmits(['result']);

watch(() => props.inputData, async () => {
  await debouncedSubmitPrediction();
}, { deep: true });

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
