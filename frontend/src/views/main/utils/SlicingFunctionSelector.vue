<template>
    <v-select
        clearable
        outlined
        class="slice-function-selector"
        :label="label"
        :value="value"
        :items="slicingFunctions"
        :item-text="extractName"
        item-value="uuid"
        :return-object="returnObject"
        @input="onInput"
        dense
        hide-details
    ></v-select>
</template>

<script setup lang="ts">


import {SlicingFunctionDTO} from '@/generated-sources';
import {storeToRefs} from "pinia";
import {useCatalogStore} from "@/stores/catalog";

const props = defineProps<{
    projectId: number,
    label: string,
    returnObject: boolean,
    value?: string
}>()

const emit = defineEmits(['update:value']);

const {slicingFunctions: slicingFunctions} = storeToRefs(useCatalogStore())

function extractName(SlicingFunctionDTO: SlicingFunctionDTO) {
    return SlicingFunctionDTO.displayName ?? SlicingFunctionDTO.name
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
