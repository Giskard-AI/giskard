<template>
  <v-select
      outlined
      class="model-selector"
      label="Model"
      :value="value"
      :items="projectModels"
      :item-text="extractModelName"
      item-value="id"
      return-object
      @input="onInput"
  ></v-select>
</template>

<script lang="ts">
import Component from "vue-class-component";
import Vue from "vue";
import axios from "axios";
import {IProjetFileModel} from "@/interfaces";
import {apiUrlJava} from "@/env";
import {Prop} from "vue-property-decorator";

@Component
export default class ModelSelector extends Vue {
  @Prop({required: true}) projectId!: number;
  projectModels: Array<IProjetFileModel> = [];
  @Prop() value?: IProjetFileModel;

  extractModelName(model: IProjetFileModel) {
    return model.name || model.file_name;
  }

  onInput(value) {
    this.$emit("update:value", value);
  }

  async mounted() {
    this.projectModels = (await axios.get<Array<IProjetFileModel>>(`${apiUrlJava}/api/v2/project/${this.projectId}/models`)).data;
  }
}
</script>

<style scoped>
.model-selector {
  min-width: 300px
}
</style>