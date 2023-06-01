<template>
    <v-select v-if="dataset"
              outlined
              clearable
              class="slice-function-selector"
              label="Column name"
              :items="availableColumns"
              hide-details
    ></v-select>
    <v-input v-else label="Column name" type="text"/>
</template>

<script setup lang="ts">


import {computed, onMounted, ref} from "vue";
import {DatasetDTO} from "@/generated-sources";
import axios from "axios";
import {apiURL} from "@/env";


const props = defineProps<{
    projectId: number,
    dataset?: string,
    columnType: string,
}>();

const emit = defineEmits(['update:value']);

const projectDatasets = ref<Array<DatasetDTO>>([])

onMounted(async () => projectDatasets.value = (await axios.get<Array<DatasetDTO>>(`${apiURL}/api/v2/project/${props.projectId}/datasets`)).data)

const selectedDataset = computed(() => projectDatasets.value.find(d => d.id === props.dataset));

const allowedType = computed(() => {
    switch (props.columnType) {
        case 'str':
            return 'text';
        case 'int':
        case 'float':
            return 'numeric';
        default:
            return null;
    }
});

const availableColumns = computed(() => {
    if (!selectedDataset.value || !allowedType.value) {
        return [];
    }
    return Object.entries(selectedDataset.value.columnTypes)
        .filter(([_, t]) => t === allowedType.value)
        .map(([k]) => k);
})
</script>

<style scoped>
.slice-function-selector {
    min-width: 200px;
    flex-grow: 1;
}
</style>
