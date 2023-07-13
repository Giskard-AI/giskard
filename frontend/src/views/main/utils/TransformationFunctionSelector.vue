<template>
    <div class="d-flex" :class="{w100: fullWidth}">
        <v-select
          :attach='attach'
          clearable
          :outlined='fullWidth'
          class='slice-function-selector'
          :label='label'
          :value='value'
          :items='availableTransformation'
          :item-text='extractName'
          item-value='uuid'
          :return-object='false'
          @input='onInput'
          :dense='fullWidth'
          hide-details
          :prepend-inner-icon="icon ? 'mdi-magic-staff' : null"
        ></v-select>
        <v-btn icon v-if="hasArguments" @click="updateArgs">
            <v-icon>settings</v-icon>
        </v-btn>
    </div>
</template>

<script setup lang="ts">


import { FunctionInputDTO, SlicingFunctionDTO } from '@/generated-sources';
import { storeToRefs } from 'pinia';
import { useCatalogStore } from '@/stores/catalog';
import { computed } from 'vue';
import { $vfm } from 'vue-final-modal';
import FunctionInputsModal from '@/views/main/project/modals/FunctionInputsModal.vue';
import { chain } from 'lodash';

const props = withDefaults(defineProps<{
  projectId?: number,
  label: string,
  fullWidth: boolean,
  value?: string,
  args?: Array<FunctionInputDTO>,
  icon: boolean,
  columnType?: string,
  columnName?: string,
  attach: string | boolean
}>(), {
  fullWidth: true,
  icon: false,
  attach: ''
});

const emit = defineEmits(['update:value', 'update:args', 'onChanged']);

const {
    transformationFunctions,
    transformationFunctionsByUuid,
    transformationFunctionsByColumnType
} = storeToRefs(useCatalogStore())

const availableTransformation = computed(() => props.columnType ? transformationFunctionsByColumnType.value[props.columnType] : transformationFunctions.value)

function extractName(SlicingFunctionDTO: SlicingFunctionDTO) {
    return SlicingFunctionDTO.displayName ?? SlicingFunctionDTO.name
}

async function onInput(value) {
    const columnNameArg = props.columnName ? {
        name: 'column_name',
        isAlias: false,
        params: [],
        type: 'str',
        value: props.columnName
    } as FunctionInputDTO : null;

    if (!value || (!transformationFunctionsByUuid.value[value].args?.length
        && (!transformationFunctionsByUuid.value[value].cellLevel || props.columnName))) {
        emit('update:value', value);
        emit('update:args', columnNameArg ? [columnNameArg] : []);
        emit('onChanged');
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
            defaultValue: {
                column_name: columnNameArg
            },
        },
        on: {
            async save(args: Array<FunctionInputDTO>) {
                emit('update:args', args);
                emit('onChanged');

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
            defaultValue: chain(props.args).keyBy('name').value(),
        },
        on: {
            async save(args: Array<FunctionInputDTO>) {
                emit('update:args', args);
                emit('onChanged');
            }
        },
        cancel: {}
    });
}

const hasArguments = computed(() => props.value &&
    (transformationFunctionsByUuid.value[props.value].args?.length || transformationFunctionsByUuid.value[props.value].cellLevel))

</script>

<style scoped>
.slice-function-selector {
    min-width: 200px;
    flex-grow: 1;
}
</style>
