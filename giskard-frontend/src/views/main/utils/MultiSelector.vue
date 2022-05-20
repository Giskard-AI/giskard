<template>
  <v-select
    v-model="selectOptions"
    :items="options"
    :label="label"
    multiple
    @change="emit"
  >
    <template v-slot:prepend-item>
      <v-list-item
        ripple
        @mousedown.prevent
        @click="toggle"
      >
        <v-list-item-action>
          <v-icon :color="selectOptions.length > 0 ? 'indigo darken-4' : ''">
            {{icon()}}
          </v-icon>
        </v-list-item-action>
        <v-list-item-content>
          <v-list-item-title>
            Select All
          </v-list-item-title>
        </v-list-item-content>
      </v-list-item>
      <v-divider class="mt-2"></v-divider>
    </template>
    <template v-slot:selection="{ item, index }">
      <v-chip v-if="index < 1">
        <span>{{ item }}</span>
      </v-chip>
      <span
        v-if="index == 1"
        class="grey--text text-caption"
      >
          (+{{ selectOptions.length - 1 }} others)
        </span>
    </template>
  </v-select>
</template>

<script lang="ts">
import Component from "vue-class-component";
import Vue from "vue";
import axios from "axios";
import {apiUrlJava} from "@/env";
import {Prop} from "vue-property-decorator";
import { DatasetDTO, ModelDTO } from '@/generated-sources';

@Component
export default class MultiSelector extends Vue {
  @Prop({required: true}) selectedOptions!: string[];
  @Prop({required: true}) options!: string[];
  @Prop({required: true}) label!: string[];
  selectOptions=this.selectedOptions;

  toggle() {
    this.$nextTick(():void=> {
      let options:string[]=[]
      if (this.selectOptions.length<this.options.length){
        options=this.options.slice() ;
      }
      this.selectOptions=options;
      this.emit(options)
    })
  }

  emit(options) {
    this.$emit("update:selectedOptions", options);
  }

  icon() {
    if (this.selectedOptions.length == this.options.length) return "mdi-close-box"
    if (this.selectedOptions.length < this.options.length) return "mdi-minus-box"
    return "mdi-checkbox-blank-outline"
  }

  async mounted() {
  }
}
</script>

<style scoped>
.dataset-selector {
  min-width: 300px
}
</style>