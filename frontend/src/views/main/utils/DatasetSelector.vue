<template>
  <v-select attach clearable outlined class='dataset-selector' :label='label' :model-value='value' :items='filteredDatasets' :item-text='extractDatasetName' :item-value="'id'" :return-object='returnObject' @input='onInput' dense hide-details></v-select>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import axios from 'axios';
import { apiURL } from '@/env';
import { DatasetDTO } from '@/generated-sources';

interface Props {
  projectId: number;
  label?: string;
  returnObject?: boolean;
  value?: string | null;
  filter: (dataset: DatasetDTO) => boolean;
}

const props = withDefaults(defineProps<Props>(), {
  returnObject: true,
  label: 'Dataset',
  value: undefined,
  filter: () => true
});

const emit = defineEmits(['update:value']);

const projectDatasets = ref<Array<DatasetDTO>>([]);

onMounted(async () => {
  projectDatasets.value = (await axios.get<Array<DatasetDTO>>(`${apiURL}/api/v2/project/${props.projectId}/datasets`)).data
});

const filteredDatasets = computed(() => projectDatasets.value?.filter(props.filter));

function extractDatasetName(dataset: DatasetDTO) {
  return dataset.name || dataset.id;
}

function onInput(value) {
  emit('update:value', value);
}
</script>

<style scoped>
.dataset-selector {
  min-width: 200px
}
</style>
