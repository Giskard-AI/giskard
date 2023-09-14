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
                                         :column-name.sync="columnFilter.columnName"
                                         :column-type.sync="columnFilter.columnType"
                                         :slicing-type.sync="columnFilter.comparisonType"
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

import { ColumnType, ComparisonClauseDTO, DatasetDTO } from '@/generated-sources';
import { ref } from 'vue';
import ColumnFilterCreator from '@/views/main/utils/ColumnFilterCreator.vue';
import { useCatalogStore } from '@/stores/catalog';

const props = defineProps<{
  projectKey: string,
  dataset: DatasetDTO
}>();

const columnFilters = ref<Array<Partial<ComparisonClauseDTO & { columnType: ColumnType }>>>([{}]);

const emit = defineEmits(['created']);

async function save(close) {
  const slicingFunction = await useCatalogStore().createSlicingFunction(props.projectKey, props.dataset, columnFilters.value);
    emit('created', slicingFunction.uuid);
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
