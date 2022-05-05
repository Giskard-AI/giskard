<template>
</template>

<script lang='ts'>
import { Component, Prop, Vue, Watch } from 'vue-property-decorator';
import { api } from '@/api';
import { readToken } from '@/store/main/getters';
import { commitAddNotification } from '@/store/main/mutations';

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
  @Prop({ required: true }) selectedFilter!: string;
  @Prop({ required: true }) currentRowIdx!: number;
  @Prop({ required: true }) minThreshold!: number;
  @Prop({ required: true }) maxThreshold!: number;

  rows: Record<string, any>[] = [];
  numberOfRows: number = 0;
  numberOfPages: number = 0;
  page: number = 0;
  itemsPerPage = 200;
  prediction: string | number | undefined = '';
  loading = false;
  errorMsg: string = '';
  rowIdxInPage: number = 0;

  async activated() {
    await this.fetchRowAndEmit(true);
  }

  async mounted() {
    await this.fetchRowAndEmit(true);
  }

  @Watch('currentRowIdx')
  async reloadOnRowIdx() {
    await this.fetchRowAndEmit(false);
  }
  @Watch('datasetId')
  @Watch('selectedFilter')
  async reloadAlways() {
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
  public async fetchRows(rowIdxInResults: number, hasFilterChanged:boolean) {
    const remainder = rowIdxInResults % this.itemsPerPage;
    const newPage = Math.floor(rowIdxInResults % this.itemsPerPage);
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
        'minThreshold': this.minThreshold,
        'maxThreshold': this.maxThreshold,
        'target': 'Default',
      };
      const response = await api.getDataFilteredByRange(readToken(this.$store),this.datasetId, props);
      this.rows = eval(response.data.data); // TODO send directly json with page from java
      this.numberOfRows = response.data.rowNb;
    } catch (error) {
      commitAddNotification(this.$store, { content: error.response.data.detail, color: 'error' });
    }
  }

  public async fetchDetails() {
    try {
      const response = await api.getDatasetDetails(readToken(this.$store), this.datasetId);
      this.numberOfRows = response.data.numberOfRows;
      this.numberOfPages = response.data.numberOfRows % this.itemsPerPage + 1;
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
