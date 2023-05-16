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
                    <v-btn color=primary @click="emit('confirm', close)">Save</v-btn>
                </v-card-actions>
            </v-card>
        </div>
    </vue-final-modal>
</template>

<script setup lang="ts">

import {ColumnFilterDTO, DatasetDTO} from "@/generated-sources";
import {ref} from "vue";
import ColumnFilterCreator from "@/views/main/utils/ColumnFilterCreator.vue";

const props = defineProps<{
    dataset: DatasetDTO
}>();

const columnFilters = ref<Array<Partial<ColumnFilterDTO>>>([{}])

const emit = defineEmits(['input']);

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
