<template>
  <div class="main">
    <LoadingFullscreen v-show="loading" name="explanation" class="pb-6" />
    <v-container class="text-center" v-show="!loading">
      <v-row v-if="Object.keys(fullExplanations).length !== 0 &&
        fullExplanations.constructor === Object
        ">
        <v-col>
          <v-chart v-if="predictionTask === ModelType.REGRESSION" class="chart" :option="chartOptionsRegression" autoresize />
          <v-chart v-if="predictionTask === ModelType.CLASSIFICATION && classificationLabels.length === 2" class="chart" :option="chartOptionsBinaryClassification" autoresize />
          <v-chart v-if="predictionTask === ModelType.CLASSIFICATION && classificationLabels.length > 2" class="chart" :option="chartOptionsMultiClassification" autoresize />
        </v-col>
      </v-row>
      <p v-if="errorMsg" class="error--text">
        {{ errorMsg }}
      </p>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from "vue";
import LoadingFullscreen from "@/components/LoadingFullscreen.vue";
import { api } from "@/api";
import { use } from "echarts/core";
import { BarChart } from "echarts/charts";
import { CanvasRenderer } from "echarts/renderers";
import { GridComponent } from "echarts/components";
import { ModelType } from "@/generated-sources";
import * as _ from "lodash";
import { CanceledError } from "axios";
import VChart from "vue-echarts";

use([CanvasRenderer, BarChart, GridComponent]);

interface Props {
  modelId: string;
  datasetId: string;
  predictionTask: string;
  targetFeature: string;
  classificationLabels: string[];
  inputData: { [key: string]: string };
  modelFeatures: string[];
  debounceTime?: number;
}

const props = withDefaults(defineProps<Props>(), {
  debounceTime: 250,
});

const loading = ref<boolean>(false);
const errorMsg = ref<string>("");
const fullExplanations = ref<any>({});
const controller = ref<AbortController | undefined>();

onMounted(async () => {
  await getExplanation();
});

watch(() => props.inputData, async () => {
  await debouncedGetExplanation();
}, { deep: true });

const debouncedGetExplanation = _.debounce(async () => {
  await getExplanation();
}, props.debounceTime);

async function getExplanation() {
  if (controller.value) {
    controller.value.abort();
  }
  controller.value = new AbortController();
  if (Object.keys(props.inputData).length) {
    try {
      loading.value = true;
      errorMsg.value = "";
      const explainResponse = (await api.explain(
        props.modelId,
        props.datasetId,
        _.pick(props.inputData, props.modelFeatures),
        controller.value
      ))
      fullExplanations.value = explainResponse.explanations;
      loading.value = false;
    } catch (error) {
      if (!(error instanceof CanceledError)) {
        errorMsg.value = error.response.data.detail;
        loading.value = false;
      }
    }
  } else {
    // reset
    errorMsg.value = "";
    fullExplanations.value = {};
  }
}

function createSimpleExplanationChart(explanation: { [name: string]: number; }) {
  const sortedExplanation = Object.entries(explanation).sort((a, b) => a[1] - b[1])
  return {
    xAxis: {
      type: "value",
      min: 0,
      name: "Feature contribution (SHAP values)",
      nameLocation: "middle",
      nameGap: 30,
    },
    yAxis: {
      type: "category",
      data: sortedExplanation.map(el => el[0]),
    },
    series: [
      {
        type: "bar",
        stack: "total",
        label: {
          show: true,
          position: "right",
          formatter: (params) =>
            params.value > 0.02
              ? params.value.toFixed(2).toLocaleString()
              : "",
        },
        labelLayout: {
          hideOverlap: true,
        },
        data: sortedExplanation.map(el => el[1]),
      },
    ],
    color: ["#0091EA"],
    grid: {
      width: "85%",
      height: "80%",
      top: "5%",
      left: "10%",
      right: "10%",
      containLabel: true,
    },
  };
}

const chartOptionsRegression = computed(() => {
  return createSimpleExplanationChart(fullExplanations.value["default"]);
});


const chartOptionsBinaryClassification = computed(() => {
  const lastExplanations =
    fullExplanations.value[Object.keys(fullExplanations.value)[Object.keys(fullExplanations.value).length - 1]];
  return createSimpleExplanationChart(lastExplanations);
});

const chartOptionsMultiClassification = computed(() => {
  const explanationSumByFeature: { [name: string]: number; } = _.reduce(
    _.values(fullExplanations.value),
    (acc, labelExplanations) => {
      _.forOwn(labelExplanations, (featureName, explainValue) => {
        acc[explainValue] = (acc[explainValue] || 0) + featureName;
      });
      return acc;
    }, {});

  // Array of features sorted by sum of SHAP explanations
  // Bonus: sort by feature name to guarantee same order if the explanation sum is the same
  const sortedTopFeatures: Array<string> = Object.entries(
    explanationSumByFeature
  ).sort((a, b) => a[1] - b[1] || b[0].localeCompare(a[0])
  ).map(el => el[0])
  let chartSeries: any[] = [];

  for (const [className, explanation] of Object.entries(
    (fullExplanations.value as { [name: string]: { [name: string]: number; }; })
  )) {
    // Guarantee that the explanation object follows the same feature order
    let explanationSortedByFeature: any = {}
    sortedTopFeatures.forEach(feature => {
      explanationSortedByFeature[feature] = explanation[feature]
    });
    chartSeries.push({
      name: className,
      type: "bar",
      stack: "total",
      emphasis: {
        focus: "series",
      },
      label: {
        show: true,
        textStyle: {
          fontSize: "10",
        },
        formatter: (params) =>
          params.value > 0.02 ? params.value.toFixed(2).toLocaleString() : "",
      },
      labelLayout: {
        hideOverlap: true,
      },
      data: Object.values(explanationSortedByFeature),
    });
  }
  return {
    xAxis: {
      type: "value",
      min: 0,
      name: "Feature contribution (SHAP values)",
      nameLocation: "middle",
      nameGap: 30,
    },
    yAxis: {
      type: "category",
      data: sortedTopFeatures,
    },
    legend: {
      data: Object.keys(fullExplanations.value),
      textStyle: {
        fontSize: "10",
      },
      type: props.classificationLabels.length > 5 ? 'scroll' : 'plain',
      top: 0,
    },
    series: chartSeries,
    grid: {
      width: "85%",
      height: "65%",
      left: "10%",
      top: "25%",
      containLabel: true,
    },
  };
});
</script>

<style scoped>
/* just so the spinner can be visible at first */
div.main {
  min-height: 100px;
}

div.center-center {
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart {
  height: 100%;
  min-height: 220px;
  width: 90%;
}
</style>
