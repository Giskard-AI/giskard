<template>
    <div class="d-flex">
        <v-select
            clearable
            outlined
            class="dataset-selector"
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
        <v-btn icon @click="openAdvancedModal">
            <v-icon>settings</v-icon>
        </v-btn>
    </div>
</template>

<script setup lang="ts">


import {onMounted, ref} from "vue";
import axios from "axios";
import {apiURL} from "@/env";
import {DatasetDTO, TestInputDTO} from '@/generated-sources';
import {$vfm} from "vue-final-modal";
import AdvancedDatasetInputModal from "@/views/main/project/modals/AdvancedDatasetInputModal.vue";

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

async function openAdvancedModal() {
    await $vfm.show({
        component: AdvancedDatasetInputModal,
        bind: {
            input: props.label
        },
        on: {
            async save(input: TestInputDTO) {

            }
        }
    });
}
</script>

<style scoped>
.dataset-selector {
  min-width: 200px
}
</style>
