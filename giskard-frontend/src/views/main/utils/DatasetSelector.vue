<template>
  <v-select
      clearable
      outlined
      class="dataset-selector"
      :label="label"
      :value="value"
      :items="projectDatasets"
      :item-text="extractDatasetName"
      item-value="id"
      :return-object="returnObject"
      @input="onInput"
  ></v-select>
</template>

<script lang="ts">
import Component from "vue-class-component";
import Vue from "vue";
import axios from "axios";
import {apiURL} from "@/env";
import {Prop} from "vue-property-decorator";
import {DatasetDTO} from '@/generated-sources';

@Component
export default class DatasetSelector extends Vue {
  @Prop({required: true}) projectId!: number;
  @Prop({default: 'Dataset', required: true}) label!: string;
  @Prop({default: true}) returnObject!: boolean;
  @Prop() value?: DatasetDTO | number;
  projectDatasets: Array<DatasetDTO> = [];

  extractDatasetName(dataset: DatasetDTO) {
    return dataset.name || dataset.fileName;
  }

  onInput(value) {
    this.$emit('update:value', value);
  }

  async mounted() {
    this.projectDatasets = (await axios.get<Array<DatasetDTO>>(`${apiURL}/api/v2/project/${this.projectId}/datasets`)).data;
  }
}
</script>

<style scoped>
.dataset-selector {
  min-width: 300px
}
</style>