<template>
    <v-row>
        <v-col cols="4">
            <v-select
                class="input-md"
                :items="columnNames"
                :value="columnName"
                @input="handleColumnNameInput"
                label="Column name"
            />
        </v-col>
        <v-col cols="4">
            <v-select
                class="input-md"
                :items="AVAILABLE_SLICING_TYPE[columnType]"
                :value="slicingType"
                @input="handleSlicingTypeInput"
                label="Condition"
                :disabled="!columnType"
            >
                <template v-slot:selection="data">
                    {{ SLICING_TYPE_DISPLAY_NAME[data.item] }}
                </template>
                <template v-slot:item="data">
                    {{ SLICING_TYPE_DISPLAY_NAME[data.item] }}
                </template>
            </v-select>
        </v-col>
        <v-col cols="4">
            <v-text-field
                class="input-md"
                v-if="columnType === ColumnType.TEXT" type="text"
                label="Value"
                :value="value"
                @input="handleValueInput"
                :disabled="!slicingType || !SLICING_TYPE_WITH_VALUE.includes(slicingType)"/>
            <v-text-field
                class="input-md"
                v-else-if="columnType === ColumnType.NUMERIC"
                label="Value"
                :value="value"
                @input="handleValueInput"
                type="number" :disabled="!slicingType"/>
            <v-select
                class="input-md"
                v-else
                :items="dataset.categoryFeatures[columnName]"
                :value="value"
                @input="handleValueInput"
                label="Value"
                :disabled="!slicingType"
            />
        </v-col>
    </v-row>

</template>

<script setup lang="ts">

import {ColumnType, DatasetDTO} from "@/generated-sources";
import {computed} from "vue";
import {NoCodeSlicingType} from "@/utils/no-code-slicing-type.enum";

const props = defineProps<{
    dataset: DatasetDTO,
    columnName?: string,
    columnType?: ColumnType,
    slicingType?: NoCodeSlicingType,
    value?: string | null
}>()

const emit = defineEmits(['update:columnName', 'update:columnType', 'update:slicingType', 'update:value']);

const columnNames = computed(() => Object.keys(props.dataset.columnTypes));

const AVAILABLE_SLICING_TYPE: { [columnType in ColumnType]: Array<NoCodeSlicingType> } = {
    [ColumnType.TEXT]: Object.values(NoCodeSlicingType),
    [ColumnType.NUMERIC]: [NoCodeSlicingType.IS, NoCodeSlicingType.IS_NOT, NoCodeSlicingType.IS_EMPTY, NoCodeSlicingType.IS_NOT_EMPTY],
    [ColumnType.CATEGORY]: [NoCodeSlicingType.IS, NoCodeSlicingType.IS_NOT, NoCodeSlicingType.IS_EMPTY, NoCodeSlicingType.IS_NOT_EMPTY],
}

const SLICING_TYPE_WITH_VALUE: Array<NoCodeSlicingType> = [
    NoCodeSlicingType.IS,
    NoCodeSlicingType.IS_NOT,
    NoCodeSlicingType.CONTAINS,
    NoCodeSlicingType.DOES_NOT_CONTAINS,
    NoCodeSlicingType.STARTS_WITH,
    NoCodeSlicingType.ENDS_WITH
];

const SLICING_TYPE_DISPLAY_NAME: { [slicingType in NoCodeSlicingType]: String } = {
    [NoCodeSlicingType.IS]: 'Equals',
    [NoCodeSlicingType.IS_NOT]: 'Is not equal',
    [NoCodeSlicingType.CONTAINS]: 'Contains',
    [NoCodeSlicingType.DOES_NOT_CONTAINS]: 'Does not contain',
    [NoCodeSlicingType.STARTS_WITH]: 'Starts with',
    [NoCodeSlicingType.ENDS_WITH]: 'Ends with',
    [NoCodeSlicingType.IS_EMPTY]: 'Is empty',
    [NoCodeSlicingType.IS_NOT_EMPTY]: 'Is not empty',
}


function handleColumnNameInput(input) {
    emit('update:columnName', input);

    if (!input) {
        emit('update:columnType', undefined);
        emit('update:slicingType', undefined);
        emit('update:value', undefined);
        return;
    }

    const columnType = props.dataset.columnTypes[input];
    emit('update:columnType', columnType);

    if (props.slicingType && !AVAILABLE_SLICING_TYPE[columnType].includes(props.slicingType)) {
        emit('update:slicingType', undefined);
        emit('update:value', undefined);
    }
}

function handleSlicingTypeInput(input) {
    emit('update:slicingType', input);

    if (!input || !SLICING_TYPE_WITH_VALUE.includes(input)) {
        emit('update:value', undefined);
        return;
    }
}

function handleValueInput(input) {
    emit('update:value', input);
}

</script>

<style scoped lang="scss">
.input-md {
    width: 16rem;
}
</style>
