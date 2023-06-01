<template>
    <v-select v-if="dataset" clearable outlined class="slice-function-selector" label="Column name" :value="value" :items="availableColumns" hide-details dense @input="v => emit('update:value', v)"></v-select>
    <v-text-field v-else label="Column name" outlined dense hide-details />
</template>

<script setup lang="ts">


import { computed, onMounted, ref } from "vue";
import { DatasetDTO } from "@/generated-sources";
import axios from "axios";
import { apiURL } from "@/env";
import { getColumnType } from "@/utils/column-type-utils";


const props = defineProps<{
    projectId: number,
    dataset?: string,
    columnType: string,
    value?: string
}>();

const emit = defineEmits(['update:value']);

const projectDatasets = ref<Array<DatasetDTO>>([])

onMounted(async () => projectDatasets.value = (await axios.get<Array<DatasetDTO>>(`${apiURL}/api/v2/project/${props.projectId}/datasets`)).data)

const selectedDataset = computed(() => projectDatasets.value.find(d => d.id === props.dataset));

const allowedType = computed(() => getColumnType(props.columnType));

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
}
</style>
