<template>
  <v-card class="mb-4" id="resultCard" outlined>
    <v-card-title>Result</v-card-title>
    <v-card-text class="text-center card-text" v-if="inputData">
      <LoadingFullscreen v-show="loading" name="result" class="pb-6" />
      <v-row v-if="prediction && isClassification(predictionTask) && !loading">
        <v-col lg="8" md="12" sm="12" xs="12" v-if="resultProbabilities && Object.keys(resultProbabilities).length > 0
          ">
          <div>Probabilities <span v-if="Object.keys(resultProbabilities).length > 5"> (5 of {{ Object.keys(resultProbabilities).length }})</span></div>
          <v-chart class="chart" :option="chartOptions" :init-options="chartInit" autoresize />
        </v-col>
        <v-col lg="4">
          <div class="mb-3">
            <div>Prediction</div>
            <v-tooltip bottom>
              <template v-slot:activator="{ on, attrs }">
                <div class="text-h6" :class="classColorPrediction" v-on="prediction.length > maxLengthDisplayedCategoryComp ? on : ''">
                  {{ abbreviateMiddle(prediction, maxLengthDisplayedCategoryComp) }}
                </div>
              </template>
              <span> {{ prediction }}</span>
            </v-tooltip>

          </div>
          <div>
            <div class="mb-2">
              <div>Actual <span v-show="isDefined(actual) && modified">(before modification)</span></div>

              <v-tooltip bottom>
                <template v-slot:activator="{ on, attrs }">
                  <div class="text-h6">
                    <div v-if="isDefined(actual)" v-on="actual.length > maxLengthDisplayedCategoryComp ? on : ''">{{ abbreviateMiddle(actual, maxLengthDisplayedCategoryComp) }}</div>
                    <div v-else>-</div>
                  </div>
                </template>
                <span>{{ actual }}</span>
              </v-tooltip>

            </div>
            <div class="caption">
              <div v-if="targetFeature">target: {{ targetFeature }}</div>
              <div v-if="model && model.threshold && (model.modelType != ModelType.CLASSIFICATION || model.classificationLabels.length == 2)">
                threshold:
                {{ model.threshold }}
              </div>
            </div>
          </div>
        </v-col>
      </v-row>
      <v-row>
      </v-row>
      <v-row v-if="prediction && predictionTask === ModelType.REGRESSION && !loading">
        <v-col lg="4">
          <div>Prediction</div>
          <div class="text-h6 success--text">
            {{ prediction | formatTwoDigits }}
          </div>
        </v-col>
        <v-col lg="4">
          <div>Actual <span v-show="isDefined(actual) && modified">(before modification)</span></div>
          <div v-if="isDefined(actual)" class="text-h6">{{ actual | formatTwoDigits }}</div>
          <div v-else>-</div>
        </v-col>
        <v-col lg="4">
          <div>Difference</div>
          <div v-if="isDefined(actual)" class="font-weight-light center-center">
            {{ ((prediction - actual) / actual) * 100 | formatTwoDigits }} %
          </div>
          <div v-else>-</div>
        </v-col>
      </v-row>
      <v-row>
        <v-col v-if="!prediction && !errorMsg && !loading">
          <p>No data yet</p>
        </v-col>
        <v-col v-if="errorMsg">
          <p class="error--text">
            {{ errorMsg }}
          </p>
        </v-col>
      </v-row>
    </v-card-text>

    <v-card-actions v-show="Object.keys(resultProbabilities).length > predCategoriesN">
      <ResultPopover :resultProbabilities='resultProbabilities' :prediction='prediction' :actual='actual' :classColorPrediction='classColorPrediction'></ResultPopover>
    </v-card-actions>

  </v-card>
</template>

<script setup lang="ts">
import VChart from 'vue-echarts';
import { computed, getCurrentInstance, onMounted, ref, watch } from 'vue';
import ResultPopover from '@/components/ResultPopover.vue';
import LoadingFullscreen from '@/components/LoadingFullscreen.vue';
import { api } from '@/api';
import { use } from 'echarts/core';
import { BarChart } from 'echarts/charts';
import { CanvasRenderer } from 'echarts/renderers';
import { GridComponent } from 'echarts/components';
import { ModelDTO, ModelType } from '@/generated-sources';
import { isClassification } from '@/ml-utils';
import { abbreviateMiddle, maxLengthDisplayedCategory } from '@/results-utils';
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
  debounceTime: 250,
});

const chartInit = {
  renderer: 'svg'
}

const prediction = ref<string | number | undefined>("");
const resultProbabilities = ref<any>({});
const loading = ref<boolean>(false);
const errorMsg = ref<string>("");
const predCategoriesN = ref<number>(5);
const controller = ref<AbortController | undefined>(undefined);
const sizeResultCard = ref<number>(0);

const actual = computed(() => {
  if (props.targetFeature && !errorMsg.value) return props.inputData[props.targetFeature]
  else return undefined
})

const isCorrectPrediction = computed(() => {
  if (_.isNumber(actual.value) || _.isNumber(prediction.value)) {
    return _.toNumber(actual.value) === _.toNumber(prediction.value);
  } else {
    return _.toString(actual.value) === _.toString(prediction.value);
  }
})

const classColorPrediction = computed(() => {
  if (actual.value === null) return 'info--text text--darken-2'
  else return isCorrectPrediction.value ? 'primary--text' : 'error--text'
})

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
      ))
      prediction.value = predictionResult.prediction;
      emit("result", prediction.value);

      resultProbabilities.value = Object.entries(predictionResult.probabilities)
        .sort(([, v1], [, v2]) => +v2 - +v1)       // Sort the object by value - solution based on:
        .reduce((r, [k, v]) => ({ ...r, [k]: v }), {}); // https://stackoverflow.com/questions/55319092/sort-a-javascript-object-by-key-or-value-es6

      errorMsg.value = "";
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
    errorMsg.value = "";
    prediction.value = undefined;
    resultProbabilities.value = {};
  }
}

const debouncedSubmitPrediction = _.debounce(async () => {
  await submitPrediction();
}, props.debounceTime);

const maxLengthDisplayedCategoryComp = computed(() => {
  return maxLengthDisplayedCategory(sizeResultCard.value);
})

const chartOptions = computed(() => {
  let results = firstNSortedByKey(resultProbabilities.value, predCategoriesN.value)
  results = sliceLongCategoryName(results, maxLengthDisplayedCategoryComp.value)
  return {
    xAxis: {
      type: "value",
      min: 0,
      max: 1,
    },
    yAxis: {
      type: "category",
      data: Object.keys(results),
      axisLabel: {
        interval: 0,
      },
    },
    series: [
      {
        type: "bar",
        label: {
          show: true,
          position: "right",
          formatter: (params: any) =>
            params.value % 1 == 0
              ? params.value
              : params.value.toFixed(2).toLocaleString(),
        },
        data: Object.values(results),
      },
    ],
    color: ["#0091EA"],
    grid: {
      width: "80%",
      height: "80%",
      top: "10%",
      left: "10%",
      right: "10%",
      containLabel: true,
    },
  };
});

function firstNSortedByKey(obj: Object, n: number) {
  let listed = Object.entries(obj)
    .sort(([, a], [, b]) => a - b)
    .slice(-n);
  return Object.fromEntries(listed)
}

function sliceLongCategoryName(obj: Object, max_size: number) {
  let res = Object.fromEntries(Object.entries(obj).map(function (elt) {
    return ["".concat(...[abbreviateMiddle(elt[0], max_size)]), elt[1]]
  }))
  return res
}

function isDefined(val: any) {
  return !_.isNil(val);
}

const emit = defineEmits(["result"]);

watch(() => props.inputData, async () => {
  await debouncedSubmitPrediction();
}, { deep: true })

onMounted(async () => {
  const clientWidth = instance?.proxy.$parent?.$el.querySelector('#resultCard')?.clientWidth;
  if (clientWidth) {
    sizeResultCard.value = clientWidth;
  }
  await submitPrediction();

  if (clientWidth) {
    window.addEventListener('resize', () => {
      sizeResultCard.value = clientWidth;
    })
  }
})
</script>

<style scoped>
div.center-center {
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart {
  height: 90%;
  min-height: 100px;
  width: 90%;
}

div.caption {
  font-size: 0.6875em !important;
  line-height: 1rem !important;
}

#labels-container {
  font-size: 10px;
  margin-top: 20px;
}

.card-text {
  position: relative;
}

.v-data-table tbody td {
  font-size: 10px !important;
}

.v-tooltip__content {
  max-width: 400px !important;
  overflow-wrap: anywhere;
}
</style>
