<template>
  <v-card class="mb-4">
    <v-card-title>Result</v-card-title>
    <v-card-text class="text-center card-text" v-if="inputData">
      <OverlayLoader :show="loading" absolute solid no-fade/>
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
                !isDefined(actual)
                  ? 'info--text text--darken-2'
                  : isCorrectPrediction
                  ? 'success--text'
                  : 'error--text'
              "
            >
              {{ prediction }}
            </div>
          </div>
          <div>
            <div class="mb-2">
              <div>Actual <span v-show="isDefined(actual) && modified">(before modification)</span></div>
              <div v-if="isDefined(actual)" class="text-h6">{{ actual }}</div>
              <div v-else>-</div>
            </div>
            <div class="caption">
              <div v-if="targetFeature">target: {{ targetFeature }}</div>
              <div v-if="model && model.threshold">threshold: {{ model.threshold }}</div>
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
        <v-col v-if="!prediction && !errorMsg"><p>No data yet</p></v-col>
        <v-col v-if="errorMsg">
          <p class="error--text">
            {{ errorMsg }}
          </p>
        </v-col>
      </v-row>
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
import {ModelDTO, ModelType} from "@/generated-sources";
import {isClassification} from "@/ml-utils";
import * as _ from "lodash";
import {CanceledError} from "axios";

use([CanvasRenderer, BarChart, GridComponent]);
Vue.component("v-chart", ECharts);

@Component({
  components: {OverlayLoader}
})
export default class PredictionResults extends Vue {
  @Prop({required: true}) model!: ModelDTO;
  @Prop({required: true}) datasetId!: number;
  @Prop({required: true}) predictionTask!: ModelType;
  @Prop() targetFeature!: string;
  @Prop() classificationLabels!: string[];
  @Prop() inputData!: { [key: string]: string };
  @Prop({default: false}) modified!: boolean;

  prediction: string | number | undefined = "";
  resultProbabilities: object = {};
  loading: boolean = false;
  errorMsg: string = "";
  isClassification = isClassification;
  ModelType = ModelType;
  predCategoriesN = 10;
  controller?: AbortController;

  async mounted() {
    await this.submitPrediction()
  }

  @Watch("inputData", {deep: true})
  private async onInputDataChange() {
    await this.debouncedSubmitPrediction();
  }

  private debouncedSubmitPrediction = _.debounce(async () => {
    await this.submitPrediction();
  }, 150);

  private async submitPrediction() {
    if (this.controller) {
      this.controller.abort();
    }
    this.controller = new AbortController();
    if (Object.keys(this.inputData).length) {
      try {
        this.loading = true;
        const predictionResult = (await api.predict(
            this.model.id,
            this.datasetId,
            this.inputData,
            this.controller
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
        this.loading = false;
      } catch (error) {
        if (!(error instanceof CanceledError)) {
          this.errorMsg = error.response.data.detail;
          this.prediction = undefined;
          this.loading = false;
        }
      }
    } else {
      // reset
      this.errorMsg = "";
      this.prediction = undefined;
      this.resultProbabilities = {};
    }
  }

  get isCorrectPrediction() {
    if (_.isNumber(this.actual) || _.isNumber(this.prediction)) {
      return _.toNumber(this.actual) === _.toNumber(this.prediction);
    } else {
      return _.toString(this.actual) === _.toString(this.prediction);
    }
  }

  get actual() {
    if (this.targetFeature && !this.errorMsg) return this.inputData[this.targetFeature]
    else return undefined
  }

  /**
   * Getting first n entries of sorted objects and sort alphabetically, aggregating for "Others" options
   *
   * @param obj object
   * @param n number of entries to keep
   * @private
   */
  private firstNSortedByKey(obj, n) {
    const numberExtraCategories = Object.keys(obj).length - n;
    let filteredObject = Object.keys(obj)
        .slice(0, n)
        .sort()
        .reduce(function (acc, current) {
          acc[current] = obj[current]
          return acc;
        }, {});
    if (numberExtraCategories > 0) {
      const sumOthers = Object.values(obj).slice(n, -1).reduce((acc: any, val: any) => acc + val, 0);
      filteredObject = {[`Others (${numberExtraCategories})`]: sumOthers, ...filteredObject};
    }
    return filteredObject;
  }

  isDefined(val: any) {
    return !_.isNil(val);
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
</style>
