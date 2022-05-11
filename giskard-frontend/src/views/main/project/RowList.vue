<template>
  <v-row v-if='selectedFilter=="CUSTOM"' style='width: 60%'>
    <v-select
      style='width: 100px;margin-left:15px'
      :items='labels'
      label='Target Label'
      v-model='targetLabel'
    ></v-select>

    <v-select
      style='width: 100px;margin-left:15px'
      :items='labels'
      label='Predicted Label'
      v-model='predictedLabel'
      step='0.001'
    ></v-select>

    <v-range-slider
      v-model='range'
      :max='1'
      :min='0'
      step='0.001'
      hide-details
      class='align-center'
      style='margin-left: 20px'
    >
      <template v-slot:prepend>
        <v-text-field
          :value='range[0]'
          step='0.001'
          class='mt-0 pt-0'
          hide-details
          single-line
          type='number'
          style='width: 60px'
          @change='$set(range, 1, $event)'
        ></v-text-field>
      </template>
      <template v-slot:append>
        <v-text-field
          :value='range[1]'
          class='mt-0 pt-0'
          hide-details
          single-line
          type='number'
          style='width: 60px'
          @change='$set(range, 1, $event)'
        ></v-text-field>
      </template>
    </v-range-slider>
  </v-row>

</template>

<script lang='ts'>
import { Component, Prop, Vue, Watch } from 'vue-property-decorator';
import { api } from '@/api';
import { readToken } from '@/store/main/getters';
import { commitAddNotification } from '@/store/main/mutations';
import { Filter, RowFilterType } from '@/generated-sources';

/**
 * TODO: This class should be on the wrapper, no template for the moment
 */
@Component({
  components: {}
})
export default class RowList extends Vue {
  //@Prop({ required: true }) selectedId!: number;
  @Prop({ required: true }) datasetId!: number;
  @Prop({ required: true }) modelId!: number;
  @Prop({ required: true }) selectedFilter!: RowFilterType;
  @Prop({ required: true }) currentRowIdx!: number;
  @Prop({ required: true }) inspectionId!: number;
  @Prop({ required: true }) shuffleMode!: number;

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
  predictedLabel: string = '';
  targetLabel: string = '';
  range: number[] = [0, 1];


  async mounted() {
    await this.fetchDetails();
    this.predictedLabel = this.labels[0];
    this.targetLabel = this.labels[0];
    await this.fetchRowAndEmit(true);
  }

  @Watch('currentRowIdx')
  async reloadOnRowIdx() {
    await this.fetchRowAndEmit(false);
  }

  //@Watch('datasetId')
  @Watch('selectedFilter')
  @Watch('range')
  @Watch('targetLabel')
  @Watch('predictedLabel')
  @Watch('shuffleMode')
  async reloadAlways() {
    console.log(this.selectedFilter == RowFilterType.CUSTOM);
    await this.fetchRowAndEmit(true);
  }

  async fetchRowAndEmit(hasFilterChanged) {
    await this.fetchRows(this.currentRowIdx, hasFilterChanged);
    const row = await this.getRow(this.currentRowIdx);
    this.$emit('fetchedRow', row, this.numberOfRows);
  }

  /**
   * Calling fetch rows if necessary, i.e. when start or end of the page
   * @param rowIdxInResults index of the row in the results
   */
  public async fetchRows(rowIdxInResults: number, hasFilterChanged: boolean) {
    const remainder = rowIdxInResults % this.itemsPerPage;
    const newPage = Math.floor(rowIdxInResults /this.itemsPerPage);
    console.log(rowIdxInResults, this.itemsPerPage, newPage, remainder)

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
      const filter:Filter = {
        'minThreshold': this.range[0],
        'maxThreshold': this.range[1],
        'targetLabel': this.targetLabel,
        'predictedLabel': this.predictedLabel,
        'rowFilter': this.selectedFilter,
      };
      const response = await api.getDataFilteredByRange(readToken(this.$store), this.datasetId, props, filter);
      this.rows = response.data.data;
      this.numberOfRows = response.data.rowNb;
    } catch (error) {
      commitAddNotification(this.$store, { content: error.response.data.detail, color: 'error' });
    }
  }

  public async fetchDetails() {
    try {
      const response = await api.getLabelsForTarget(readToken(this.$store), this.inspectionId);
      this.labels = response.data;
    } catch (error) {
      commitAddNotification(this.$store, { content: error.response.data.detail, color: 'error' });
    }
  }
}
</script>

<style scoped>
.v-data-table ::v-deep tr.v-data-table__selected {
  background: #0097a7 !important;
}

.v-data-table >>> tbody > tr {
  cursor: pointer;
}
</style>
