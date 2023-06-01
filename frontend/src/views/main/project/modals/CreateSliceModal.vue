<template>
    <vue-final-modal
        v-slot="{ close }"
        v-bind="$attrs"
        classes="modal-container"
        content-class="modal-content"
        v-on="$listeners"
    >
        <div class="text-center">
            <v-card>
                <v-card-title>
                    Create new slice for "{{ dataset.name ?? dataset.id }}"
                </v-card-title>
                <v-card-text>
                    <ColumnFilterCreator v-for="(columnFilter, idx) in columnFilters"
                                         :key="idx"
                                         :dataset="dataset"
                                         :column-name.sync="columnFilter.column"
                                         :column-type.sync="columnFilter.columnType"
                                         :slicing-type.sync="columnFilter.slicingType"
                                         :value.sync="columnFilter.value"
                    />
                </v-card-text>
                <v-card-actions>
                    <div class="flex-grow-1"/>
                    <v-btn color="secondary" @click="close">Cancel</v-btn>
                    <v-btn color=primary @click="save(close)">Save</v-btn>
                </v-card-actions>
            </v-card>
        </div>
    </vue-final-modal>
</template>

<script setup lang="ts">

import {ColumnFilterDTO, DatasetDTO, NoCodeSlicingType, SlicingFunctionDTO} from "@/generated-sources";
import {ref} from "vue";
import ColumnFilterCreator from "@/views/main/utils/ColumnFilterCreator.vue";
import {v4 as uuidv4} from 'uuid';
import {useCatalogStore} from "@/stores/catalog";

const props = defineProps<{
    dataset: DatasetDTO
}>();

const columnFilters = ref<Array<Partial<ColumnFilterDTO>>>([{}])

const emit = defineEmits(['created']);

const CLAUSE_BUILDERS: { [clause in NoCodeSlicingType]: (column: string, value: string) => string } = {
    [NoCodeSlicingType.IS]: (column, value) => `giskard.slicing.slice.EqualTo(${column}, ${value}, equal=False)`,
    [NoCodeSlicingType.IS_NOT]: (column, value) => `giskard.slicing.slice.NotEqualTo(${column}, ${value}, equal=False)`,
    [NoCodeSlicingType.CONTAINS]: (column, value) => `giskard.slicing.slice.StringClause(${column}, ${value}, 'contains')`,
    [NoCodeSlicingType.DOES_NOT_CONTAINS]: (column, value) => `giskard.slicing.slice.StringClause(${column}, ${value}, 'contains', isNot=True)`,
    [NoCodeSlicingType.STARTS_WITH]: (column, value) => `giskard.slicing.slice.StringClause(${column}, ${value}, 'startswith')`,
    [NoCodeSlicingType.ENDS_WITH]: (column, value) => `giskard.slicing.slice.StringClause(${column}, ${value}, 'endswith')`,
    [NoCodeSlicingType.IS_EMPTY]: (column, _) => `giskard.slicing.slice.EqualTo(${column}, float('NaN'))`,
    [NoCodeSlicingType.IS_NOT_EMPTY]: (column, _) => `giskard.slicing.slice.NotEqualTo(${column}, float('NaN'))`,
}

const CLAUSE_SYMBOLS: { [clause in NoCodeSlicingType]: string } = {
    [NoCodeSlicingType.IS]: '==',
    [NoCodeSlicingType.IS_NOT]: '!=',
    [NoCodeSlicingType.CONTAINS]: 'contains',
    [NoCodeSlicingType.DOES_NOT_CONTAINS]: 'does not contain',
    [NoCodeSlicingType.STARTS_WITH]: 'startswith',
    [NoCodeSlicingType.ENDS_WITH]: 'endswith',
    [NoCodeSlicingType.IS_EMPTY]: 'is empty',
    [NoCodeSlicingType.IS_NOT_EMPTY]: 'is not empty',
}

const NO_VALUES = [NoCodeSlicingType.IS_EMPTY, NoCodeSlicingType.IS_NOT_EMPTY]

function escapePython(val?: string | number | null): string {
    if (typeof val === 'string') {
        return `'${val.replace("'", "\\'")}'`
    } else {
        return val ? val.toString() : 'None'
    }
}

function clauseCode(clause: ColumnFilterDTO) {
    return CLAUSE_BUILDERS[clause.slicingType](escapePython(clause.column), escapePython(clause.value))
}

function clausesCode() {
    return `[${columnFilters.value.map((v) => clauseCode(v as ColumnFilterDTO)).join(', ')}]`
}

function clauseToString(clause: ColumnFilterDTO) {
    return `${escapePython(clause.column)} ${CLAUSE_SYMBOLS[clause.slicingType]} ${NO_VALUES.includes(clause.slicingType) ? '' : escapePython(clause.value)}`
}

async function save(close) {
    const name = columnFilters.value.map((v) => clauseToString(v as ColumnFilterDTO)).join(' & ')

    const dto: SlicingFunctionDTO = {
        uuid: uuidv4(),
        args: [],
        code: `giskard.slicing.slice.Query(${clausesCode()})`,
        displayName: name,
        doc: 'Automatically generated slicing function',
        module: '',
        moduleDoc: '',
        name,
        potentiallyUnavailable: false,
        tags: ['pickle', 'ui'],
        version: null,
        cellLevel: false,
        columnType: '',
        noCode: true
    }

    await useCatalogStore().saveSlicingFunction(dto)

    emit('created', dto.uuid);

    close()
}

</script>

<style scoped>
::v-deep(.modal-container) {
    display: flex;
    justify-content: center;
    align-items: center;
}

::v-deep(.modal-content) {
    position: relative;
    display: flex;
    flex-direction: column;
    margin: 0 1rem;
    padding: 1rem;
}

</style>
