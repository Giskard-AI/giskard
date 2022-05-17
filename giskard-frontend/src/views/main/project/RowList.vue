<template>
  <v-container style='margin-left:15px'>
    <v-row>
      <v-col cols='12' md='3'>
        <v-select
          :items='filterTypes'
          label='Filter'
          v-model='selectedFilter'
        ></v-select>
      </v-col>
    </v-row>

    <v-row v-if='inspection!=null && inspection.predictionTask!="classification" && selectedFilter=="CUSTOM"'>
      <v-col cols="12" md='3'>
        <v-subheader>Predicted value is between</v-subheader>
      </v-col>
      <v-col cols='12' md='1'>
        <v-text-field
          :value='minThreshold'
          step='0.001'
          hide-details
          type='number'
          @change='(val)=>{this.minThreshold=val;}'
        ></v-text-field>
      </v-col>
      <v-col cols="12" md='1'>
        <v-subheader>and</v-subheader>
      </v-col>
      <v-col cols='12' md='1'>
        <v-text-field
          :value='maxThreshold'
          step='0.001'
          hide-details
          type='number'
          @change='(val)=>{this.maxThreshold=val;}'
        ></v-text-field>
      </v-col>
    </v-row>

    <v-row v-if='inspection!=null && inspection.predictionTask!="classification" && selectedFilter=="CUSTOM"'>
      <v-col cols="12" md='3'>
        <v-subheader>Actual value is between</v-subheader>
      </v-col>
      <v-col cols='12' md='1'>
        <v-text-field
          :value='minActualThreshold'
          step='0.001'
          hide-details
          type='number'
          @change='(val)=>{this.minActualThreshold=val;}'
        >
        </v-text-field>
      </v-col>
      <v-col cols="12" md='1'>
        <v-subheader>and</v-subheader>
      </v-col>
      <v-col cols='12' md='1'>
        <v-text-field
          :value='maxActualThreshold'
          step='0.001'
          hide-details
          type='number'
          @change='(val)=>{this.maxActualThreshold=val;}'
        ></v-text-field>
      </v-col>
    </v-row>
    <v-row v-if='selectedFilter=="CUSTOM" && inspection.predictionTask=="classification" '>
      <v-col cols='12' md='3'>
        <MultiSelector label='Actual Labels' :options='labels' :selected-options='targetLabel' @update='(options)=>{this.predictedLabel=options}'></MultiSelector>
      </v-col>
      <v-col cols='12' md='3'>
        <MultiSelector label='Predicted Labels' :options='labels' :selected-options='predictedLabel' @update='(options)=>{this.predictedLabel=options}'></MultiSelector>
      </v-col>
    </v-row>
    <v-row v-if='selectedFilter=="CUSTOM" && inspection.predictionTask=="classification" '>
      <v-col cols="12" md='2'>
        <v-subheader>Probability of</v-subheader>
      </v-col>
      <v-col cols='12' md='3'>
        <v-select
          :items='labels'
          v-model='thresholdLabel'
          hide-details
        ></v-select>
      </v-col>
      <v-col cols="12" md='2'>
        <v-subheader>is between : </v-subheader>
      </v-col>
      <v-col cols='12' md='2'>
        <v-text-field
          label='Min Threshold'
          :value='minThreshold'
          step='0.001'
          hide-details
          type='number'
          @change='(val)=>{this.minThreshold=val;}'
        ></v-text-field>
      </v-col>
      <v-col cols="12" md='1'>
        <v-subheader> and </v-subheader>
      </v-col>
      <v-col cols='12' md='2'>
        <v-text-field
          label='Max Threshold'
          :value='maxThreshold'
          step='0.001'
          hide-details
          type='number'
          @change='(val)=>{this.maxThreshold=val;}'
        ></v-text-field>
      </v-col>
    </v-row>
  </v-container>
</template>

<script lang='ts'>
import { Component, Prop, Vue, Watch } from 'vue-property-decorator';
import { api } from '@/api';
import { readToken } from '@/store/main/getters';
import { commitAddNotification } from '@/store/main/mutations';
import { Filter, InspectionDTO, RegressionUnit, RowFilterType } from '@/generated-sources';
import MultiSelector from '@/views/main/utils/MultiSelector.vue';

/**
 * TODO: This class should be on the wrapper, no template for the moment
 */
@Component({
  components: { MultiSelector }
})
export default class RowList extends Vue {
  //@Prop({ required: true }) selectedId!: number;
  @Prop({ required: true }) datasetId!: number;
  @Prop({ required: true }) modelId!: number;
  @Prop({ required: true }) currentRowIdx!: number;
  @Prop({ required: true }) inspectionId!: number;
  @Prop({ required: true }) shuffleMode!: boolean;

  rows: Record<string, any>[] = [];
  numberOfRows: number = 0;
  numberOfPages: number = 0;
  page: number = 0;
  itemsPerPage = 200;
  prediction: string | number | undefined = '';
  loading = false;
  errorMsg: string = '';
  rowIdxInPage: number = 0;
  labels: string[] = [];
  predictedLabel: string[] = [];
  targetLabel: string[] = [];
  minThreshold= null;
  maxThreshold = null;
  inspection = {} as InspectionDTO;
  allFilterTypes = Object.values(RowFilterType);
  filterTypes = this.allFilterTypes;
  selectedFilter = this.filterTypes[0];
  regressionThreshold: number = 0.1;
  regressionUnits = Object.keys(RegressionUnit);
  percentRegressionUnit = true;
  thresholdLabel: string = '';
  minActualThreshold=null;
  maxActualThreshold=null;

  async mounted() {
    await this.fetchDetails();
    if (this.inspection.predictionTask != 'classification') {
      this.filterTypes = [RowFilterType.ALL, RowFilterType.CORRECT, RowFilterType.WRONG, RowFilterType.CUSTOM];
    }
    this.thresholdLabel = this.labels[0];
    await this.fetchRowAndEmit(true);
    this.predictedLabel = [];
    this.targetLabel = [];
  }

  @Watch('currentRowIdx')
  async reloadOnRowIdx() {
    await this.fetchRowAndEmit(false);
  }

  @Watch('inspectionId')
  @Watch('regressionThreshold')
  @Watch('selectedFilter')
  @Watch('minThreshold')
  @Watch('maxThreshold')
  @Watch('minActualThreshold')
  @Watch('maxActualThreshold')
  @Watch('targetLabel')
  @Watch('predictedLabel')
  @Watch('shuffleMode')
  @Watch('percentRegressionUnit')
  async reloadAlways() {
    console.log("ee")
    await this.fetchRowAndEmit(true);

  }

  async fetchRowAndEmit(hasFilterChanged) {
    await this.fetchRows(this.currentRowIdx, hasFilterChanged);
    const row = await this.getRow(this.currentRowIdx);
    this.$emit('fetchedRow', row, this.numberOfRows, hasFilterChanged);
  }

  /**
   * Calling fetch rows if necessary, i.e. when start or end of the page
   * @param rowIdxInResults index of the row in the results
   */
  public async fetchRows(rowIdxInResults: number, hasFilterChanged: boolean) {
    const remainder = rowIdxInResults % this.itemsPerPage;
    const newPage = Math.floor(rowIdxInResults / this.itemsPerPage);
    if (remainder == 0 || hasFilterChanged) {
      await this.fetchRowsByRange(newPage * this.itemsPerPage, (newPage + 1) * this.itemsPerPage);
    }
  }

  /**
   * Selecting row in the page
   * @param rowIdxInResults row's index in
   */
  public async getRow(rowIdxInResults) {
    const remainder = rowIdxInResults % this.itemsPerPage;
    this.rowIdxInPage = remainder;
    return this.rows[this.rowIdxInPage];
  }


  /**
   * Requesting the filtered rows in a given range
   * @param minRange
   * @param maxRange
   */
  public async fetchRowsByRange(minRange: number, maxRange: number) {
    try {
      const props = {
        'modelId': this.modelId,
        'minRange': minRange,
        'maxRange': maxRange,
        'isRandom': this.shuffleMode
      };
      const filter: Filter = {
        maxLabelThreshold: this.maxActualThreshold!,
        minLabelThreshold: this.minActualThreshold!,
        'minThreshold': this.minThreshold!,
        'maxThreshold': this.maxThreshold!,
        'targetLabel': this.targetLabel,
        'predictedLabel': this.predictedLabel,
        'rowFilter': this.selectedFilter,
        'regressionUnit': this.percentRegressionUnit ? RegressionUnit.ABSDIFFPERCENT : RegressionUnit.ABSDIFF,
        'thresholdLabel': this.thresholdLabel

      };
      const response = await api.getDataFilteredByRange(readToken(this.$store), this.inspectionId, props, filter);
      this.rows = response.data.data;
      this.numberOfRows = response.data.rowNb;
    } catch (error) {
      commitAddNotification(this.$store, { content: error.response.data.detail, color: 'error' });
    }
  }

  public async fetchDetails() {
    try {
      const response = await api.getLabelsForTarget(readToken(this.$store), this.inspectionId);
      const responseInspection = await api.getInspection(readToken(this.$store), this.inspectionId);
      this.labels = response.data;
      this.inspection = responseInspection.data;

    } catch (error) {
      commitAddNotification(this.$store, { content: error.response.data.detail, color: 'error' });
    }
  }
}
</script>
<style scoped>
.v-slider {
  margin-top: 20px !important;
}
</style>
