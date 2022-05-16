<template>
  <v-select
    v-model="selectedOptions"
    :items="options"
    :label="label"
    multiple
  >
    <template v-slot:prepend-item>
      <v-list-item
        ripple
        @mousedown.prevent
        @click="toggle"
      >
        <v-list-item-action>
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
      <v-chip v-if="index <= 1">
        <span>{{ item }}</span>
      </v-chip>
      <span
        v-if="index >= 2"
        class="grey--text text-caption"
      >
          (+{{ selectedOptions.length - 1 }} others)
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
export default class DatasetSelector extends Vue {
  @Prop({required: true}) selectedOptions!: string[];
  @Prop({required: true}) options!: string[];
  @Prop({required: true}) label!: string[];

  toggle () {
    this.$nextTick(():void=> {
      if (this.selectedOptions.length>=this.options.length) {
        this.selectedOptions = []
      } else {
        this.selectedOptions = this.options.slice()
      }
    })
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