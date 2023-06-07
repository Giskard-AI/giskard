<template>
  <div>
    <v-list-item v-for="[input, value] in Object.entries(inputs)" :key="input">
      <v-list-item-content>
        <v-list-item-title>{{ input }}</v-list-item-title>
        <v-list-item-subtitle> {{ formatInputValue(input, value) }}</v-list-item-subtitle>
      </v-list-item-content>
    </v-list-item>
  </div>
</template>

<script setup lang="ts">

import {DatasetDTO, ModelDTO} from '@/generated-sources';

const {inputs, inputTypes, models, datasets} = defineProps<{
  inputs: { [key: string]: string },
  inputTypes: { [key: string]: string },
  models: { [key: string]: ModelDTO },
  datasets: { [key: string]: DatasetDTO }
}>();

function formatInputValue(input: string, value: string): string {
  switch (inputTypes[input]) {
    case 'Dataset':
        return datasets[value].name ?? 'Unnamed dataset';
      case 'BaseModel':
          return models[value].name;
      default:
          return value;
  }
}

</script>
