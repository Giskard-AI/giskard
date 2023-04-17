<template>
  <div class="main">
    <OverlayLoader :show="loading" solid absolute no-fade/>
    <v-container class="text-center">
      <v-row
          v-if="
          Object.keys(fullExplanations).length !== 0 &&
          fullExplanations.constructor === Object
        "
      >
        <v-col>
          <v-chart
              v-if="predictionTask === ModelType.REGRESSION"
              class="chart"
              :option="chartOptionsRegression"
              autoresize
          />
          <v-chart
              v-if="predictionTask === ModelType.CLASSIFICATION && classificationLabels.length === 2"
              class="chart"
              :option="chartOptionsBinaryClassification"
              autoresize
          />
          <v-chart
              v-if="predictionTask === ModelType.CLASSIFICATION && classificationLabels.length > 2"
              class="chart"
              :option="chartOptionsMultiClassification"
              autoresize
          />
        </v-col>
      </v-row>
      <p v-if="errorMsg" class="error--text">
        {{ errorMsg }}
      </p>
    </v-container>
  </div>
</template>

<script lang="ts">
import {Component, Prop, Vue, Watch} from "vue-property-decorator";
import OverlayLoader from "@/components/OverlayLoader.vue";
import {api} from "@/api";
import ECharts from "vue-echarts";
import {use} from "echarts/core";
import {BarChart} from "echarts/charts";
import {CanvasRenderer} from "echarts/renderers";
import {GridComponent} from "echarts/components";
import "echarts/lib/component/legend";
import {ModelType} from "@/generated-sources";
import _ from "lodash";
import {CanceledError} from "axios";

use([CanvasRenderer, BarChart, GridComponent]);
Vue.component("v-chart", ECharts);

@Component({
  components: {OverlayLoader},
})
export default class PredictionExplanations extends Vue {
  @Prop({required: true}) modelId!: string;
  @Prop({required: true}) datasetId!: string;
  @Prop({required: true}) predictionTask!: string;
  @Prop() targetFeature!: string;
  @Prop() classificationLabels!: string[];
  @Prop({default: {}}) inputData!: object;
  @Prop() modelFeatures!: string[];
  @Prop({default: 250}) debounceTime!: number;


  loading: boolean = false;
  errorMsg: string = "";
  fullExplanations: object = {};
  ModelType = ModelType;
  controller?: AbortController;

  async mounted() {
    await this.getExplanation()
  }

  @Watch("inputData", {deep: true})
  private async onInputDataChange() {
    await this.debouncedGetExplanation();
  }

  private debouncedGetExplanation = _.debounce(async () => {
    await this.getExplanation();
  }, this.debounceTime);

  private async getExplanation() {
    if (this.controller) {
      this.controller.abort();
    }
    this.controller = new AbortController();
    if (Object.keys(this.inputData).length) {
      try {
        this.loading = true;
        this.errorMsg = "";
        const explainResponse = await api.explain(
            this.modelId,
            this.datasetId,
            _.pick(this.inputData, this.modelFeatures),
            this.controller
        )
        this.fullExplanations = explainResponse.explanations;
        this.loading = false;
      } catch (error) {
        if (!(error instanceof CanceledError)) {
          this.errorMsg = error.response.data.detail;
          this.loading = false;
        }
      }
    } else {
      // reset
      this.errorMsg = "";
      this.fullExplanations = {};
    }
  }

  private createSimpleExplanationChart(explanation: object) {
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

  get chartOptionsRegression() {
    return this.createSimpleExplanationChart(this.fullExplanations["default"]);
  }

  get chartOptionsBinaryClassification() {
    const lastExplanations =
        this.fullExplanations[Object.keys(this.fullExplanations)[Object.keys(this.fullExplanations).length - 1]];
    return this.createSimpleExplanationChart(lastExplanations);
  }

  get chartOptionsMultiClassification() {
    const explanationSumByFeature: { [name: string]: number; } = _.reduce(
        _.values(this.fullExplanations),
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
    let chartSeries: object[] = [];

    for (const [className, explanation] of Object.entries(
        this.fullExplanations
    )) {
      // Guarantee that the explanation object follows the same feature order
      let explanationSortedByFeature: object = {}
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
        data: Object.keys(this.fullExplanations),
        textStyle: {
          fontSize: "10",
        },
        type: this.classificationLabels.length > 5 ? 'scroll' : 'plain',
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
  }
}
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
