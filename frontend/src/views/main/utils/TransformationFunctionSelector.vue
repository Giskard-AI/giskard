<template>
    <div class="d-flex w100">
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
        <v-btn icon v-if="hasArguments" @click="updateArgs">
            <v-icon>settings</v-icon>
        </v-btn>
    </div>
</template>

<script setup lang="ts">


import {FunctionInputDTO, SlicingFunctionDTO} from '@/generated-sources';
import {storeToRefs} from "pinia";
import {useCatalogStore} from "@/stores/catalog";
import {computed} from "vue";
import {$vfm} from "vue-final-modal";
import FunctionInputsModal from "@/views/main/project/modals/FunctionInputsModal.vue";

const props = defineProps<{
    projectId: number,
    label: string,
    value?: string,
    args?: Array<FunctionInputDTO>
}>()

const emit = defineEmits(['update:value', 'update:args']);

const {transformationFunctions, transformationFunctionsByUuid} = storeToRefs(useCatalogStore())

function extractName(SlicingFunctionDTO: SlicingFunctionDTO) {
    return SlicingFunctionDTO.displayName ?? SlicingFunctionDTO.name
}

async function onInput(value) {
    if (!value) {
        emit('update:value', value);
        return;
    }

    const previousValue = props.value;
    emit('update:value', value);

    const func = transformationFunctionsByUuid.value[value];
    await $vfm.show({
        component: FunctionInputsModal,
        bind: {
            projectId: props.projectId,
            title: `Set up parameters for '${func.displayName ?? func.name}'`,
            function: func,
            defaultValue: [],
        },
        on: {
            async save(args: Array<FunctionInputDTO>) {
                emit('update:args', args);
            },
            async cancel() {
                // Rollback changes
                emit('update:value', previousValue)
            }
        },
        cancel: {}
    });
}

async function updateArgs() {
    const func = transformationFunctionsByUuid.value[props.value!];
    await $vfm.show({
        component: FunctionInputsModal,
        bind: {
            projectId: props.projectId,
            title: `Update parameters for '${func.displayName ?? func.name}'`,
            function: func,
            defaultValue: [],
        },
        on: {
            async save(args: Array<FunctionInputDTO>) {
                emit('update:args', args);
            },
            async cancel() {
                // Rollback changes
                emit('update:args', props.args);
            }
        },
        cancel: {}
    });
}

const hasArguments = computed(() => props.value && transformationFunctionsByUuid.value[props.value].args.length > 0)
</script>

<style scoped>
.slice-function-selector {
    min-width: 200px;
    flex-grow: 1;
}
</style>
