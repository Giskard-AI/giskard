<template>
  <v-select
      outlined
      class="model-selector"
      label="Model"
      :value="value"
      :items="projectModels"
      :item-text="extractModelName"
      :item-value="'id'"
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
import {ModelDTO} from '@/generated-sources';

@Component
export default class ModelSelector extends Vue {
  @Prop({required: true}) projectId!: number;
  @Prop({default: true}) returnObject!: boolean;
  projectModels: Array<ModelDTO> = [];
  @Prop() value?: ModelDTO | number;

  extractModelName(model: ModelDTO) {
    return model.name || model.fileName;
  }

  onInput(value) {
    this.$emit("update:value", value);
  }

  async mounted() {
    this.projectModels = (await axios.get<Array<ModelDTO>>(`${apiURL}/api/v2/project/${this.projectId}/models`)).data;
  }
}
</script>

<style scoped>
.model-selector {
  min-width: 300px
}
</style>