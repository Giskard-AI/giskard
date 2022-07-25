<template>
  <v-card class='mb-4'>
    <OverlayLoader v-show='loading' />
    <v-card-title>Result</v-card-title>
    <v-card-text class='text-center' v-if='inputData'>
      <v-row v-if='prediction && isClassification(predictionTask)'>
        <v-col
          lg='8'
          md='12'
          sm='12'
          xs='12'
          v-if='
            resultProbabilities && Object.keys(resultProbabilities).length > 0
          '
        >
          <div>Probabilities</div>
          <v-chart class='chart' :option='chartOptions' autoresize />
        </v-col>
        <v-col lg='4'>
          <div class='mb-3'>
            <div>Prediction</div>
            <div
              class='text-h6'
              :class="
                !isDefined(actual)
                  ? 'info--text text--darken-2'
                  : prediction === actual
                  ? 'success--text'
                  : 'error--text'
              "
            >
              {{ prediction }}
            </div>
          </div>
          <div>

            <div class='mb-2'>
              <div>Actual <span v-show='isDefined(actual) && modified'>(before modification)</span></div>
              <div class='targetFeedbackDiv' v-if='isDefined(actual) && targetMetaData'>
                <div class='text-h6'></div>
                <v-form lazy-validation>
                    <ValidationProvider
                      :name="targetMetaData.name"
                      v-slot="{ dirty }"
                    >
                      <div class="py-1 d-flex">
                        <input type="number" v-if="targetMetaData.type === 'numeric'"
                               v-model="inputData[targetMetaData.name]"
                               class="common-style-input"
                               :class="{'is-dirty': dirty || inputData[targetMetaData.name] !== originalData[targetMetaData.name]}"
                               @change="$emit('update:inputData', inputData)"
                               required
                        />
                        <textarea v-if="targetMetaData.type === 'text'"
                                  v-model="inputData[targetMetaData.name]"
                                  :rows="!inputData[targetMetaData.name] ? 1 : Math.min(15, parseInt(inputData[targetMetaData.name].length / 40) + 1)"
                                  class="common-style-input"
                                  :class="{'is-dirty': dirty || inputData[targetMetaData.name] !== originalData[targetMetaData.name]}"
                                  @change="$emit('update:inputData', inputData)"
                                  required
                        ></textarea>
                        <select v-if="targetMetaData.type === 'category'"
                                v-model="inputData[targetMetaData.name]"
                                class="common-style-input"
                                :class="{'is-dirty': dirty || inputData[targetMetaData.name] !== originalData[targetMetaData.name]}"
                                @change="$emit('update:inputData', inputData)"
                                required
                        >
                          <option v-for="k in targetMetaData.values" :key="k" :value="k">{{ k }}</option>
                        </select>
                        <FeedbackPopover
                          v-if="true"
                          :inputLabel="targetFeature"
                          :inputValue="inputData[targetFeature]"
                          :originalValue="originalData[targetFeature]"
                          inputType="category"
                          :feedback-type='FeedbackType.TARGET'
                          v-on="$listeners"
                        />
                      </div>
                    </ValidationProvider>
                </v-form>
              </div>
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
      <v-row v-if='prediction && predictionTask === ModelType.REGRESSION'>
        <v-col lg='4'>
          <div>Prediction</div>
          <div class='text-h6 success--text'>
            {{ prediction | formatTwoDigits }}
          </div>
        </v-col>
        <v-col lg="4">
          <div>Actual <span v-show="isDefined(actual) && modified">(before modification)</span></div>
          <div v-if="isDefined(actual)" class="text-h6">{{ actual | formatTwoDigits }}</div>
          <div v-else>-</div>
        </v-col>
        <v-col lg='4'>
          <div>Difference</div>
          <div v-if="isDefined(actual)" class="font-weight-light center-center">
            {{ ((prediction - actual) / actual) * 100 | formatTwoDigits }} %
          </div>
          <div v-else>-</div>
        </v-col>
      </v-row>
      <p v-if='!prediction && !errorMsg'>No data yet</p>
      <p v-if='errorMsg' class='error--text'>
        {{ errorMsg }}
      </p>
    </v-card-text>
  </v-card>
</template>

<script lang='ts'>
import { Component, Prop, Vue, Watch } from 'vue-property-decorator';
import OverlayLoader from '@/components/OverlayLoader.vue';
import { api } from '@/api';
import ECharts from 'vue-echarts';
import { use } from 'echarts/core';
import { BarChart } from 'echarts/charts';
import { CanvasRenderer } from 'echarts/renderers';
import { GridComponent } from 'echarts/components';
import { DatasetDTO, FeatureMetadataDTO, ModelDTO, ModelType,FeedbackType} from '@/generated-sources';
import { isClassification } from '@/ml-utils';
import * as _ from 'lodash';
import FeedbackPopover from '@/components/FeedbackPopover.vue';
import * as _ from "lodash";

use([CanvasRenderer, BarChart, GridComponent]);
Vue.component('v-chart', ECharts);

@Component({
  components: { FeedbackPopover, OverlayLoader }
})
export default class PredictionResults extends Vue {
  @Prop({ required: true }) model!: ModelDTO;
  @Prop({required: true}) datasetId!: number;
  @Prop({ required: true }) predictionTask!: ModelType;
  @Prop({ required: true }) inputMetaData!: FeatureMetadataDTO[];
  @Prop() targetFeature!: string;
  @Prop() classificationLabels!: string[];
  @Prop() inputData!: {[key: string]: string};
  @Prop({ required: true }) originalData!: object;
  @Prop({ default: false }) modified!: boolean;
  FeedbackType=FeedbackType;


  prediction: string | number | undefined = '';
  resultProbabilities: object = {};
  loading: boolean = false;
  errorMsg: string = '';
  isClassification = isClassification;
  ModelType = ModelType;
  predCategoriesN = 10;
  targetMetaData;

  async mounted() {
    this.targetMetaData=this.inputMetaData.filter(e=>e.name==this.targetFeature)[0]
    await this.submitPrediction();
  }

  isDirty() {
    return !_.isEqual(this.inputData[this.targetFeature], this.originalData[this.targetFeature]);
  }

  @Watch('inputData', { deep: true })
  public async submitPrediction() {
    if (Object.keys(this.inputData).length) {
      try {
        this.loading = true;
        const predictionResult = (await api.predict(
          this.model.id,
            this.datasetId,
          this.inputData
        ));
        this.prediction = predictionResult.prediction;
        this.$emit('result', this.prediction);
        this.resultProbabilities = predictionResult.probabilities;
        // Sort the object by value - solution based on:
        // https://stackoverflow.com/questions/55319092/sort-a-javascript-object-by-key-or-value-es6
        this.resultProbabilities = Object.entries(this.resultProbabilities)
          .sort(([, v1], [, v2]) => +v2 - +v1)
          .reduce((r, [k, v]) => ({ ...r, [k]: v }), {});
        this.errorMsg = '';
      } catch (error) {
        this.errorMsg = error.response.data.detail;
        this.prediction = undefined;
      } finally {
        this.loading = false;
      }
    } else {
      // reset
      this.errorMsg = '';
      this.prediction = undefined;
      this.resultProbabilities = {};
    }
  }

  get actual() {
    if (this.targetFeature && !this.errorMsg) return this.inputData[this.targetFeature];
    else return undefined;
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
      .reduce(function(acc, current) {
        acc[current] = obj[current];
        return acc;
      }, {});
    if (numberExtraCategories > 0) {
      const sumOthers = Object.values(obj).slice(n, -1).reduce((acc: any, val: any) => acc + val, 0);
      filteredObject = { [`Others (${numberExtraCategories})`]: sumOthers, ...filteredObject };
    }
    return filteredObject;
  }
  isDefined(val:any){
    return !_.isNil(val);
  }
  get chartOptions() {
    const results = this.firstNSortedByKey(this.resultProbabilities, this.predCategoriesN);
    return {
      xAxis: {
        type: 'value',
        min: 0,
        max: 1
      },
      yAxis: {
        type: 'category',
        data: Object.keys(results),
        axisLabel: {
          interval: 0
        }
      },
      series: [
        {
          type: 'bar',
          label: {
            show: true,
            position: 'right',
            formatter: (params) =>
              params.value % 1 == 0
                ? params.value
                : params.value.toFixed(2).toLocaleString()
          },
          data: Object.values(results)
        }
      ],
      color: ['#0091EA'],
      grid: {
        width: '80%',
        height: '80%',
        top: '10%',
        left: '10%',
        right: '10%',
        containLabel: true
      }
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

.v-data-table tbody td {
  font-size: 10px !important;
}
.targetFeedbackDiv >>> select{
  flex-grow: 1;
}


.common-style-input {
  flex-grow: 1;
  border: 1px solid #e4e4e4;
  border-radius: 5px;
  line-height: 24px;
  min-height: 24px;
  width: 56%;
}

select.common-style-input {
  /* -moz-appearance: menulist-button;
  -webkit-appearance: menulist-button; */
  /* OR */
  -moz-appearance: none;
  -webkit-appearance: none;
  appearance: none;
  background-image: url('data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22292.4%22%20height%3D%22292.4%22%3E%3Cpath%20fill%3D%22%23007CB2%22%20d%3D%22M287%2069.4a17.6%2017.6%200%200%200-13-5.4H18.4c-5%200-9.3%201.8-12.9%205.4A17.6%2017.6%200%200%200%200%2082.2c0%205%201.8%209.3%205.4%2012.9l128%20127.9c3.6%203.6%207.8%205.4%2012.8%205.4s9.2-1.8%2012.8-5.4L287%2095c3.5-3.5%205.4-7.8%205.4-12.8%200-5-1.9-9.2-5.5-12.8z%22%2F%3E%3C%2Fsvg%3E');
  background-repeat: no-repeat, repeat;
  background-position: right .3em top 50%, 0 0;
  background-size: .65em auto, 100%;
}

.common-style-input.is-dirty {
  background-color: #AD14572B; /* accent color but with opacity */
}

</style>
