<template>
  <v-select
      outlined
      class="dataset-selector"
      :label="label"
      :value="value"
      :items="projectDatasets"
      :item-text="extractDatasetName"
      item-value="id"
      return-object
      @input="onInput"
  ></v-select>
</template>

<script lang="ts">
import Component from "vue-class-component";
import Vue from "vue";
import axios from "axios";
import {apiUrlJava} from "@/env";
import {Prop} from "vue-property-decorator";
import { DatasetDTO, ModelDTO } from '@/generated-sources';

@Component
export default class DatasetSelector extends Vue {
  @Prop({required: true}) projectId!: number;
  @Prop({default: 'Dataset', required: true}) label!: string;
  @Prop() value?: DatasetDTO;
  projectDatasets: Array<DatasetDTO> = [];

  extractDatasetName(dataset: DatasetDTO) {
    console.log(dataset)
    return dataset.name || dataset.file_name;
  }

  onInput(value) {
    this.$emit("update:value", value);
  }

  async mounted() {
    this.projectDatasets = (await axios.get<Array<ModelDTO>>(`${apiUrlJava}/api/v2/project/datasets`, {params: {projectId: this.projectId}})).data;
  }
}
</script>

<style scoped>
.dataset-selector {
  min-width: 300px
}
</style>