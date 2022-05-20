<template>
  <v-container style='margin-left:15px' v-if="inspection">
    <v-row>
      <v-col cols='12' md='3'>
        <v-select
            :items='filterTypes'
            label='Filter'
            v-model='selectedFilter'
            item-value="out"
            item-text="in"
        ></v-select>
      </v-col>
    </v-row>
    <v-row
        v-if='inspection.model && isClassification(inspection.model.modelType) && selectedFilter===RowFilterType.CUSTOM'>
      <v-col cols='12' md='3'>
        <v-subheader class='pt-5 pl-0'>Actual value is between</v-subheader>
      </v-col>
      <v-col cols='12' md='1'>
        <v-text-field
            :value='minActualThreshold'
            hide-details
            step='0.001'
            type='number'
            @change='(val)=>{this.minActualThreshold=val;}'
        >
        </v-text-field>
      </v-col>
      <v-col cols='12' md='1'>
        <v-subheader class='pt-5'>and</v-subheader>
      </v-col>
      <v-col cols='12' md='1'>
        <v-text-field
            :value='maxActualThreshold'
            hide-details
            step='0.001'
            type='number'
            @change='(val)=>{this.maxActualThreshold=val;}'
        ></v-text-field>
      </v-col>
    </v-row>
    <v-row
        v-if='inspection.model && isClassification(inspection.model.modelType) && selectedFilter===RowFilterType.CUSTOM'>
      <v-col cols='12' md='3'>
        <v-subheader class='pt-5 pl-0'>Predicted value is between</v-subheader>
      </v-col>
      <v-col cols='12' md='1'>
        <v-text-field
            :value='minThreshold'
            hide-details
            step='0.001'
            type='number'
            @change='(val)=>{this.minThreshold=val;}'
        ></v-text-field>
      </v-col>
      <v-col cols='12' md='1'>
        <v-subheader class='pt-5'>and</v-subheader>
      </v-col>
      <v-col cols='12' md='1'>
        <v-text-field
            :value='maxThreshold'
            hide-details
            step='0.001'
            type='number'
            @change='(val)=>{this.maxThreshold=val;}'
        ></v-text-field>
      </v-col>
    </v-row>


    <v-row
        v-if='selectedFilter===RowFilterType.CUSTOM && inspection.model && isClassification(inspection.model.modelType) '>
      <v-col cols='12' md='3'>
        <MultiSelector label='Actual Labels' :options='inspection.model.classificationLabels'
                       :selected-options.sync='targetLabel'></MultiSelector>
      </v-col>
      <v-col cols='12' md='3'>
        <MultiSelector label='Predicted Labels' :options='inspection.model.classificationLabels'
                       :selected-options.sync='predictedLabel'></MultiSelector>
      </v-col>
    </v-row>
    <v-row v-if='selectedFilter===RowFilterType.CUSTOM && isClassification(inspection.model.modelType) '>
      <v-col cols='12' md='2' class='pl-0 pt-5'>
        <v-subheader>Probability of</v-subheader>
      </v-col>
      <v-col cols='12' md='3'>
        <v-select
            v-model='thresholdLabel'
            :items='inspection.model.classificationLabels'
            hide-details
        ></v-select>
      </v-col>
      <v-col cols='12' md='2'>
        <v-subheader class='justify-center pt-5 '>is between :</v-subheader>
      </v-col>
      <v-col cols='12' md='2'>
        <v-text-field
            :value='minThreshold'
            hide-details
            label='Min Threshold'
            step='0.001'
            type='number'
            @change='(val)=>{this.minThreshold=val;}'
        ></v-text-field>
      </v-col>
      <v-col cols='12' md='1'>
        <v-subheader class='justify-center pt-5'> and</v-subheader>
      </v-col>
      <v-col cols='12' md='2'>
        <v-text-field
            :value='maxThreshold'
            hide-details
            label='Max Threshold'
            step='0.001'
            type='number'
            @change='(val)=>{this.maxThreshold=val;}'
        ></v-text-field>
      </v-col>
    </v-row>
  </v-container>
</template>

<script lang='ts'>
import {Component, Prop, Vue, Watch} from 'vue-property-decorator';
import {api} from '@/api';
import {commitAddNotification} from '@/store/main/mutations';
import {Filter, InspectionDTO, RegressionUnit, RowFilterType} from '@/generated-sources';
import MultiSelector from '@/views/main/utils/MultiSelector.vue';
import {isClassification} from '@/ml-utils';

/**
 * TODO: This class should be on the wrapper, no template for the moment
 */
@Component({
  components: {MultiSelector}
})
export default class RowList extends Vue {
  //@Prop({ required: true }) selectedId!: number;
  @Prop({required: true}) inspection!: InspectionDTO;
  @Prop({required: true}) currentRowIdx!: number;
  @Prop({required: true}) shuffleMode!: boolean;

  rows: Record<string, any>[] = [];
  numberOfRows: number = 0;
  numberOfPages: number = 0;
  page: number = 0;
  itemsPerPage = 200;
  prediction: string | number | undefined = '';
  loading = false;
  errorMsg: string = '';
  rowIdxInPage: number = 0;
  predictedLabel: string[] = [];
  targetLabel: string[] = [];
  minThreshold = null;
  maxThreshold = null;
  filterTypes: any[] = [];
  selectedFilter = RowFilterType.ALL;
  regressionThreshold: number = 0.1;
  percentRegressionUnit = true;
  thresholdLabel?: string = undefined;
  minActualThreshold = null;
  maxActualThreshold = null;
  classificationFiltersMap = [
    {out: RowFilterType.ALL, in: "All"},
    {out: RowFilterType.CORRECT, in: "Correct Predictions"},
    {out: RowFilterType.WRONG, in: "Incorrect Predictions"},
    {out: RowFilterType.BORDERLINE, in: "Borderline"},
    {out: RowFilterType.CUSTOM, in: "Custom"}
  ];
  regressionFiltersMap = [
    {out: RowFilterType.ALL, in: "All"},
    {out: RowFilterType.CORRECT, in: "Closest predictions (top 15%)"},
    {out: RowFilterType.WRONG, in: "Most distant predictions (top 15%)"},
    {out: RowFilterType.CUSTOM, in: "Custom"}
  ];
  isClassification = isClassification;
  RowFilterType = RowFilterType;

  async mounted() {
    this.filterTypes = isClassification(this.inspection.model.modelType) ? this.classificationFiltersMap : this.regressionFiltersMap
    this.selectedFilter = this.filterTypes[0].out;
    this.thresholdLabel = this.inspection.model.classificationLabels[0];
    await this.fetchRowAndEmit(true);
    this.predictedLabel = [];
    this.targetLabel = [];
    // this.loaded = true;
  }

  @Watch('currentRowIdx')
  async reloadOnRowIdx() {
    await this.fetchRowAndEmit(false);
  }

  @Watch('inspection.id')
  @Watch('regressionThreshold')
  @Watch('selectedFilter')
  @Watch('minThreshold')
  @Watch('maxThreshold')
  @Watch('minActualThreshold')
  @Watch('maxActualThreshold')
  @Watch('shuffleMode')
  @Watch('percentRegressionUnit')
  @Watch('targetLabel', {deep: true})
  @Watch('predictedLabel', {deep: true})
  @Watch('thresholdLabel' )
  async reloadAlways(nv, ov) {
    if (JSON.stringify(nv) === JSON.stringify(ov)) {
      return;
    }
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
   * @param hasFilterChanged
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
    this.rowIdxInPage = rowIdxInResults % this.itemsPerPage;
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
        'rowFilter': this.selectedFilter!,
        'regressionUnit': this.percentRegressionUnit ? RegressionUnit.ABSDIFFPERCENT : RegressionUnit.ABSDIFF,
        'thresholdLabel': this.thresholdLabel!

      };
      const response = await api.getDataFilteredByRange(this.inspection.id, props, filter);
      this.rows = response.data.data;
      this.numberOfRows = response.data.rowNb;
    } catch (error) {
      commitAddNotification(this.$store, {content: error.response.data.detail, color: 'error'});
    }
  }
}
</script>