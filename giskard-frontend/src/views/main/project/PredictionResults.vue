<template>
  <v-card class="mb-4">
    <OverlayLoader v-show="loading"/>
    <v-card-title>Result</v-card-title>
    <v-card-text class="text-center" v-if="inputData">
      <v-row v-if="prediction && isClassification(predictionTask)">
        <v-col
            lg="8"
            md="12"
            sm="12"
            xs="12"
            v-if="
            resultProbabilities && Object.keys(resultProbabilities).length > 0
          "
        >
          <div>Probabilities</div>
          <v-chart class="chart" :option="chartOptions" autoresize/>
        </v-col>
        <v-col lg="4">
          <div class="mb-3">
            <div>Prediction</div>
            <div
                class="text-h6"
                :class="
                !actual
                  ? 'info--text text--darken-2'
                  : prediction === actualForDisplay
                  ? 'success--text'
                  : 'error--text'
              "
            >
              {{ prediction }}
            </div>
          </div>
          <div>
            <div class="mb-2">
              <div>Actual <span v-show="actual && modified">(before modification)</span></div>
              <div v-if="actual" class="text-h6">{{ actualForDisplay }}</div>
              <div v-else>-</div>
            </div>
            <div class="caption">
              <div v-if="targetFeature">target: {{ targetFeature }}</div>
              <div v-if="model && model.threshold">threshold: {{ model.threshold }}</div>
              <div v-if="actual">{{ labelsAndValues }}</div>
            </div>
          </div>
        </v-col>
      </v-row>
      <v-row>
      </v-row>
      <v-row v-if="prediction && predictionTask === ModelType.REGRESSION">
        <v-col lg="4">
          <div>Prediction</div>
          <div class="text-h6 success--text">
            {{ prediction | formatTwoDigits }}
          </div>
        </v-col>
        <v-col lg="4">
          <div>Actual <span v-show="actual && modified">(before modification)</span></div>
          <div v-if="actual" class="text-h6">{{ actual | formatTwoDigits }}</div>
          <div v-else>-</div>
        </v-col>
        <v-col lg="4">
          <div>Difference</div>
          <div v-if="actual" class="font-weight-light center-center">
            {{ ((prediction - actual) / actual) * 100 | formatTwoDigits }} %
          </div>
          <div v-else>-</div>
        </v-col>
      </v-row>
      <p v-if="!prediction && !errorMsg">No data yet</p>
      <p v-if="errorMsg" class="error--text">
        {{ errorMsg }}
      </p>
    </v-card-text>
  </v-card>
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
import {ModelDTO, ModelType, PredictionDTO} from "@/generated-sources";
import {isClassification} from "@/ml-utils";

use([CanvasRenderer, BarChart, GridComponent]);
Vue.component("v-chart", ECharts);

@Component({
  components: {OverlayLoader}
})
export default class PredictionResults extends Vue {
  @Prop({required: true}) model!: ModelDTO;
  @Prop({required: true}) predictionTask!: ModelType;
  @Prop() targetFeature!: string;
  @Prop() classificationLabels!: string[];
  @Prop() inputData!: object;
  @Prop({default: false}) modified!: boolean;

  prediction: string | number | undefined = "";
  resultProbabilities: object = {};
  loading: boolean = false;
  errorMsg: string = "";
  isClassification = isClassification;
  ModelType = ModelType;
  predCategoriesN = 10;

  async mounted() {
    await this.submitPrediction()
  }

  @Watch("inputData", {deep: true})
  public async submitPrediction() {
    if (Object.keys(this.inputData).length) {
      try {
        this.loading = true;
        const predictionResult = (await api.predict(
            this.model.id,
            this.inputData
        ))
        this.prediction = predictionResult.prediction;
        this.$emit("result", this.prediction);
        this.resultProbabilities = predictionResult.probabilities
        // Sort the object by value - solution based on:
        // https://stackoverflow.com/questions/55319092/sort-a-javascript-object-by-key-or-value-es6
        this.resultProbabilities = Object.entries(this.resultProbabilities)
            .sort(([, v1], [, v2]) => +v2 - +v1)
            .reduce((r, [k, v]) => ({...r, [k]: v}), {});
        this.errorMsg = "";
      } catch (error) {
        this.errorMsg = error.response.data.detail;
        this.prediction = undefined;
      } finally {
        this.loading = false;
      }
    } else {
      // reset
      this.errorMsg = "";
      this.prediction = undefined;
      this.resultProbabilities = {};
    }
  }

  get actual() {
    if (this.targetFeature && !this.errorMsg) return this.inputData[this.targetFeature]
    else return undefined
  }

  get actualForDisplay() {
    if (this.actual) {
      if (isNaN(parseInt(this.actual.toString()))) return this.actual;
      else return this.classificationLabels[parseInt(this.actual.toString())];
    } else return "";
  }

  get labelsAndValues() {
    if (this.classificationLabels)
      return this.classificationLabels
          .map((e, idx) => `${idx}: ${e}`)
          .join(", ");
    else return "";
  }

  /**
   * Getting first n entries of sorted objects and sort alphabetically, aggregating for "Others" options
   *
   * @param obj object
   * @param n number of entries to keep
   * @private
   */
  private firstNSortedByKey(obj, n) {
    const numberExtraCategories=Object.keys(obj).length-n;
    let filteredObject=Object.keys(obj)
      .slice(0,n)
      .sort()
      .reduce(function(acc, current) {
        acc[current] = obj[current]
        return acc;
      }, {});
    if (numberExtraCategories > 0) {
      const sumOthers = Object.values(obj).slice(n, -1).reduce((acc: any, val: any) => acc + val, 0);
      filteredObject={[`Others (${numberExtraCategories})`] : sumOthers,...filteredObject };
    }
    return filteredObject;
  }

  get chartOptions() {
    const results = this.firstNSortedByKey(this.resultProbabilities, this.predCategoriesN)
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
        }
      },
      series: [
        {
          type: "bar",
          label: {
            show: true,
            position: "right",
            formatter: (params) =>
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
  }

}
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
  font-size: 11px !important;
  line-height: 1rem !important;
}
</style>
