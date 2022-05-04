<template>
  <div>
    <v-container fluid>
      <v-data-table
        dense
        single-select
        @click:row='rowClick'
        :items='rows'
        :headers='tableHeaders'
        :page.sync='page'
        :options.sync='options'
        :items-per-page='itemsPerPage'
        :server-items-length='numberOfRows'
        :pageCount='numberOfPages'
        item-key='Index'
        item-class='text-truncate'
      >
      </v-data-table>
      <v-pagination
        v-model='page'
        :length='pageCount'
      ></v-pagination>
    </v-container>
  </div>
</template>

<script lang='ts'>
import { Component, Prop, Vue, Watch } from 'vue-property-decorator';
import { api } from '@/api';
import { readToken } from '@/store/main/getters';
import { commitAddNotification } from '@/store/main/mutations';
import { read } from 'fs';

/**
 * TODO: This class should be on the wrapper
 */
@Component({
  components: {}
})
export default class RowList extends Vue {
  @Prop({ required: true }) selectedId!: number;
  @Prop({ required: true }) datasetId!: number;
  @Prop({ required: true }) modelId!: number;
  @Prop({ required: true }) selectedFilter!: string;

  rows: Record<string, any>[] = [];
  numberOfRows: number = 0;
  numberOfPages: number = 0;
  page: number = 0;
  itemsPerPage = 5;
  options = {};
  prediction: string | number | undefined = "";
  loading=false
  errorMsg: string = "";


  async activated() {
    await this.fetchRows();
  }

  async mounted() {
    await this.fetchDetails();
    await this.fetchRows();
  }

  rowClick(item, row) {
    row.select(true);
    this.selectedId = item.Index;
    this.$emit('currentRow', row );
  }

  get tableHeaders() {
    if (this.rows.length == 0) {
      return [];
    }
    const headers: Record<string, any> = this.rows[0];
    const tableHeaders = (Object.keys(headers) as Array<string>).map(header => {
      return {
        text: header,
        sortable: false, value: header, align: 'center'
      };
    });
    console.log(tableHeaders);
    return tableHeaders;
  }

  // @Watch("rows", { deep: true })
  // public async submitPredictions() {
  //   if (Object.keys(this.rows).length) {
  //     try {
  //       const resp = await api.predictDf(
  //         readToken(this.$store),
  //         this.modelId,
  //         this.rows
  //       );
  //       this.prediction = resp.data.prediction;
  //
  //       this.errorMsg = "";
  //     } catch (error) {
  //       this.errorMsg = error.response.data.detail;
  //       this.prediction = undefined;
  //     } finally {
  //       this.loading = false;
  //     }
  //   } else {
  //     // reset
  //     this.errorMsg = "";
  //     this.prediction = undefined;
  //   }}

  @Watch('datasetId')
  async reloadOnDataset() {
    await this.fetchRows();
  }

  @Watch('options')
  async reload() {
    await this.fetchRows();
  }

  @Watch('selectedFilter')
  async reloadOnFilterChange() {
    await this.fetchRows();
  }

  public async fetchRows() {
    try {
      const props={"datasetId": this.datasetId, "modelId":this.modelId, "minRange":this.page * this.itemsPerPage,
       "maxRange" : (this.page + 1) * this.itemsPerPage,
       "threshold": 0.5,// TODO get respMetadata.classification_threshold
        "target": "Default",
        filter:this.selectedFilter,
        "token":readToken(this.$store)}
      // TODO Restore the ** annotation
      const response = await api.getDataFilteredByRange(props.token,props.datasetId, props.modelId,props.target, props.threshold, props.filter, props.minRange, props.maxRange );
      this.rows = eval(response.data.data)
      this.numberOfRows=response.data.rowNb
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
