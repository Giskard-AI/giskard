<template>
  <v-select
      clearable
      hide-details="auto"
      dense
      v-model="selectOptions"
      :items="options"
      :label="label"
      multiple
      chips
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
            {{ icon() }}
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
  </v-select>
</template>

<script lang="ts">
import Component from "vue-class-component";
import Vue from "vue";
import {Prop} from "vue-property-decorator";

@Component
export default class MultiSelector extends Vue {
  @Prop({required: true}) selectedOptions!: string[];
  @Prop({required: true}) options!: string[];
  @Prop({required: true}) label!: string[];
  selectOptions = this.selectedOptions;

  toggle() {
    this.$nextTick((): void => {
      let options: string[] = []
      if (this.selectOptions.length < this.options.length) {
        options = this.options.slice();
      }
      this.selectOptions = options;
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
}
</script>
