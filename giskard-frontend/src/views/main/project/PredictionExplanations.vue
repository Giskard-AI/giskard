<template>
  <div class="main">
    <OverlayLoader v-show="loading" />
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
            v-if="predictionTask === ModelType.BINARY_CLASSIFICATION"
            class="chart"
            :option="chartOptionsBinaryClassification"
            autoresize
          />
          <v-chart
            v-if="predictionTask === ModelType.MULTICLASS_CLASSIFICATION"
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
import {readToken} from "@/store/main/getters";
import ECharts from "vue-echarts";
import {use} from "echarts/core";
import {BarChart} from "echarts/charts";
import {CanvasRenderer} from "echarts/renderers";
import {GridComponent} from "echarts/components";
import "echarts/lib/component/legend";
import {ExplainResponseDTO, ModelType} from "@/generated-sources";

use([CanvasRenderer, BarChart, GridComponent]);
Vue.component("v-chart", ECharts);

@Component({
  components: { OverlayLoader },
})
export default class PredictionExplanations extends Vue {
  @Prop({ required: true }) modelId!: number;
  @Prop({ required: true }) datasetId!: number;
  @Prop({ required: true }) predictionTask!: string;
  @Prop() targetFeature!: string;
  @Prop() classificationLabels!: string[];
  @Prop({ default: {} }) inputData!: object;

  loading: boolean = false;
  errorMsg: string = "";
  fullExplanations: object = {};
  ModelType=ModelType;

  mounted() {
    this.getExplanation()
  }
  
  @Watch("inputData", { deep: true })
  public async getExplanation() {
    if (Object.keys(this.inputData).length) {
      try {
        this.loading = true;
        this.errorMsg = "";
        const explainResponse = await api.explain(
            this.modelId,
            this.datasetId,
            this.inputData
        )
        this.fullExplanations = explainResponse.explanations;
      } catch (error) {
        this.errorMsg = error.response.data.detail;
      } finally {
        this.loading = false;
      }
    } else {
      // reset
      this.errorMsg = "";
      this.fullExplanations = {};
    }
  }

  private createSimpleExplanationChart(explanation: object) {
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
        data: Object.keys(explanation!),
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
          data: Object.values(explanation!),
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
    return this.createSimpleExplanationChart(this.fullExplanations!["default"]);
  }

  get chartOptionsBinaryClassification() {
    const lastExplanations =
      this.fullExplanations[
        Object.keys(this.fullExplanations!)[
          Object.keys(this.fullExplanations!).length - 1
        ]
      ];
    return this.createSimpleExplanationChart(lastExplanations);
  }

  get chartOptionsMultiClassification() {
    const firstExplanations =
      this.fullExplanations[Object.keys(this.fullExplanations!)[0]];
    let chartSeries: object[] = [];
    for (const [className, explanation] of Object.entries(
      this.fullExplanations
    )) {
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
        data: Object.values(explanation!),
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
        data: Object.keys(firstExplanations!),
      },
      legend: {
        data: Object.keys(this.fullExplanations),
        textStyle: {
          fontSize: "10",
        },
      },
      series: chartSeries,
      grid: {
        width: "85%",
        height: "65%",
        left: "10%",
        top: "15%",
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
  height: 90%;
  min-height: 180px;
  width: 90%;
}
</style>
