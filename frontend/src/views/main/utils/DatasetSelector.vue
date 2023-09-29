<template>
  <div class="d-flex">
    <v-select attach clearable outlined class='dataset-selector' :label='label' v-model='value'
              :items='filteredDatasets'
              :item-text='extractDatasetName' :item-value="'id'" :return-object='returnObject' @input='onInput' dense
              hide-details :disabled="disabled"></v-select>
    <v-tooltip bottom>
      <template v-slot:activator="{ on, attrs }">
        <v-btn icon :disabled="!value" v-bind="attrs" v-on="on" @click="exploreDataset">
          <v-icon>mdi-open-in-new</v-icon>
        </v-btn>
      </template>
      <span>Explore dataset</span>
    </v-tooltip>

  </div>

</template>

<script setup lang="ts">
import {computed, onMounted, ref} from 'vue';
import axios from 'axios';
import {apiURL} from '@/env';
import {DatasetDTO} from '@/generated-sources';
import router from "@/router";

interface Props {
  projectId: number;
  label?: string;
  returnObject?: boolean;
  value?: string | null;
  filter: (dataset: DatasetDTO) => boolean;
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  returnObject: true,
  label: 'Dataset',
  value: undefined,
  filter: () => true,
  disabled: false
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

function exploreDataset() {
  const routeData = router.resolve({name: 'project-catalog-datasets', query: {dataset: props.value}});
  window.open(routeData.href, '_blank');
}
</script>

<style scoped>
.dataset-selector {
  min-width: 200px
}
</style>
