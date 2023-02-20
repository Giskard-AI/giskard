<template>
  <v-list>
    <v-list-item v-for="input in inputs" :track-by="input" class="pl-0 pr-0">
      <v-row>
        <v-col>
          <v-list-item-content>
            <v-list-item-title>{{ input.name }}</v-list-item-title>
            <v-list-item-subtitle class="text-caption">{{ input.type }}</v-list-item-subtitle>
          </v-list-item-content>
        </v-col>
        <v-col>
          <DatasetSelector :project-id="projectId" :label="input.name" :return-object="false"
                           v-if="input.type === 'Dataset'" :value.sync="props.modelValue[input.name]"/>
          <ModelSelector :project-id="projectId" :label="input.name" :return-object="false"
                         v-if="input.type === 'Model'" :value.sync="props.modelValue[input.name]"/>
          <v-text-field
              :step='input.type === "float" ? 0.1 : 1'
              v-model="props.modelValue[input.name]"
              v-if="['float', 'int'].includes(input.type)"
              hide-details
              single-line
              type="number"
              outlined
              dense
          />
        </v-col>
      </v-row>
    </v-list-item>
  </v-list></template>

<script setup lang="ts">
import DatasetSelector from '@/views/main/utils/DatasetSelector.vue';
import ModelSelector from '@/views/main/utils/ModelSelector.vue';
import {computed} from 'vue';

const props = defineProps<{
  projectId: number,
  inputs: { [name: string]: string },
  modelValue: { [name: string]: any }
}>();

const inputs = computed(() => Object.keys(props.inputs).map((name) => ({
  name,
  type: props.inputs[name]
})));

</script>
