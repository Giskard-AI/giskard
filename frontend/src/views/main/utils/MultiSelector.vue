<template>
  <v-select clearable hide-details="auto" dense v-model="selectOptions" :items="options" :label="label" multiple chips @change="emitWithOptions">
    <template v-slot:prepend-item>
      <v-list-item ripple @mousedown.prevent @click="toggle">
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

<script setup lang="ts">
import { ref, getCurrentInstance } from 'vue';

const instance = getCurrentInstance();

interface Props {
  selectedOptions: string[];
  options: string[];
  label: string;
}

const props = defineProps<Props>();

const selectOptions = ref<string[]>(props.selectedOptions.slice());

const emit = defineEmits(["update:selectedOptions"]);

function toggle() {
  instance?.proxy?.$nextTick((): void => {
    let options: string[] = []
    if (selectOptions.value.length < props.options.length) {
      options = props.options.slice();
    }
    selectOptions.value = options;
    emitWithOptions(options);
  })
}

function emitWithOptions(options: string[]) {
  emit("update:selectedOptions", options);
}

function icon() {
  if (selectOptions.value.length == props.options.length) return "mdi-close-box"
  if (selectOptions.value.length < props.options.length) return "mdi-minus-box"
  return "mdi-checkbox-blank-outline"
}
</script>
