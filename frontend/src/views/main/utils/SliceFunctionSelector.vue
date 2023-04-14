<template>
    <v-select
        clearable
        outlined
        class="slice-function-selector"
        :label="label"
        :value="value"
        :items="sliceFunctions"
        :item-text="extractName"
        item-value="uuid"
        :return-object="returnObject"
        @input="onInput"
        dense
        hide-details
    ></v-select>
</template>

<script setup lang="ts">


import {SliceFunctionDTO} from '@/generated-sources';
import {storeToRefs} from "pinia";
import {useCatalogStore} from "@/stores/catalog";

const props = defineProps<{
    projectId: number,
    label: string,
    returnObject: boolean,
    value?: string
}>()

const emit = defineEmits(['update:value']);

const {sliceFunctions} = storeToRefs(useCatalogStore())

function extractName(sliceFunctionDTO: SliceFunctionDTO) {
    return sliceFunctionDTO.displayName ?? sliceFunctionDTO.name
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
