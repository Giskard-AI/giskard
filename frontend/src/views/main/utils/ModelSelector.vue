<template>
  <v-select attach clearable outlined class='model-selector' :label='label' :model-value='value' :items='projectModels' :item-text='extractModelName' :item-value="'id'" :return-object='returnObject' @input='onInput' dense hide-details></v-select>
</template>

<script setup lang="ts">
import axios from 'axios';
import { apiURL } from '@/env';
import { ModelDTO } from '@/generated-sources';
import { ref, onMounted } from 'vue';

interface Props {
  projectId: number;
  returnObject?: boolean;
  label?: string;
  value?: string | null;
}

const props = withDefaults(defineProps<Props>(), {
  returnObject: true,
  label: 'Model',
  value: undefined,
})

const projectModels = ref<Array<ModelDTO>>([]);

function extractModelName(model: ModelDTO) {
  return model.name || model.id;
}

const emit = defineEmits(["update:value"]);

function onInput(value) {
  emit("update:value", value);
}

onMounted(async () => {
  projectModels.value = (await axios.get<Array<ModelDTO>>(`${apiURL}/api/v2/project/${props.projectId}/models`)).data;
})
</script>

<style scoped>
.model-selector {
  min-width: 200px
}
</style>
