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
import { RowDetails } from '@/interfaces';

@Component({
  components: {}
})
export default class RowList extends Vue {
  //@Prop({ required: true }) projectId!: number;
  @Prop({ required: true }) datasetId!: number;

  rows: Record<string, any>[] = [];
  numberOfRows: number = 0;
  numberOfPages: number = 0;
  page: number = 0;
  itemsPerPage = 5;
  options = {};
  selectedId: number = 0;

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

  @Watch('datasetId')
  async reloadOnDataset() {
    await this.fetchRows();
  }

  @Watch('options')
  async reload() {
    await this.fetchRows();
  }

  public async fetchRows() {
    try {
      const response = await api.getDataByRange(readToken(this.$store), this.datasetId, this.page * this.itemsPerPage, (this.page + 1) * this.itemsPerPage);
      this.rows = response.data;
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
