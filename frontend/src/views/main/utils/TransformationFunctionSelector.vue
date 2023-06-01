<template>
    <div>
        <v-select
            clearable
            outlined
            class="slice-function-selector"
            :label="label"
            :value="value"
            :items="transformationFunctions"
            :item-text="extractName"
            item-value="uuid"
            :return-object="false"
            @input="onInput"
            dense
            hide-details
        ></v-select>
        <v-btn icon v-if="hasArguments">
            <v-icon>settings</v-icon>
        </v-btn>
    </div>
</template>

<script setup lang="ts">


import {SlicingFunctionDTO} from '@/generated-sources';
import {storeToRefs} from "pinia";
import {useCatalogStore} from "@/stores/catalog";
import {computed} from "vue";

const props = defineProps<{
    projectId: number,
    label: string,
    value?: string
}>()

const emit = defineEmits(['update:value']);

const {transformationFunctions, transformationFunctionsByUuid} = storeToRefs(useCatalogStore())

function extractName(SlicingFunctionDTO: SlicingFunctionDTO) {
    return SlicingFunctionDTO.displayName ?? SlicingFunctionDTO.name
}

function onInput(value) {
    emit('update:value', value);
}

const hasArguments = computed(() => props.value && transformationFunctionsByUuid[props.value].args.length > 0)
</script>

<style scoped>
.slice-function-selector {
    min-width: 200px
}
</style>
