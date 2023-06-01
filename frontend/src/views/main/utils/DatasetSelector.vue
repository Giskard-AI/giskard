<template>
    <v-select
        clearable
        outlined
        class="slice-function-selector"
        :label="label"
        :value="value"
        :items="projectDatasets"
        :item-text="extractDatasetName"
        item-value="id"
        :return-object="returnObject"
        @input="onInput"
        dense
        hide-details
    ></v-select>
</template>

<script setup lang="ts">


import {onMounted, ref} from "vue";
import axios from "axios";
import {apiURL} from "@/env";
import {DatasetDTO} from '@/generated-sources';

const props = defineProps<{
    projectId: number,
    label: string,
    returnObject: boolean,
    value?: string
}>()

const emit = defineEmits(['update:value']);

const projectDatasets = ref<Array<DatasetDTO>>([])

onMounted(async () => projectDatasets.value = (await axios.get<Array<DatasetDTO>>(`${apiURL}/api/v2/project/${props.projectId}/datasets`)).data)

function extractDatasetName(dataset: DatasetDTO) {
    return dataset.name || dataset.id;
}

function onInput(value) {
    emit('update:value', value);
}
</script>

<style scoped>
.slice-function-selector {
    min-width: 200px
}
</style>
