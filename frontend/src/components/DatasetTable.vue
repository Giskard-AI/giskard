<template>
    <v-data-table
        :headers="headers"
        :items="rows?.content"
        :server-items-length="rows?.totalItems"
        :options.sync="options"
        :item-class="rowClasses"
        :loading="!rows"
        :footer-props="{
            'items-per-page-options': [5, 10, 15, 20]
          }"
        class="elevation-1"
    >
        <template v-for="header in headers"
                  v-slot:[`item.${header.value}`]="{ header, value, item }">
            <v-tooltip bottom v-if="modificationsMap.hasOwnProperty(item['_GISKARD_INDEX_'])
                  && modificationsMap[item['_GISKARD_INDEX_']].hasOwnProperty(header.text)">
                <template v-slot:activator="{ on, attrs }">
                    <div class="modified-cell" v-bind="attrs"
                         @click="() => openDiff(value, modificationsMap[item['_GISKARD_INDEX_']][header.text])"
                         v-on="on">{{ modificationsMap[item['_GISKARD_INDEX_']][header.text] }}
                    </div>
                </template>
                <div>Click to open diff tools</div>
            </v-tooltip>
            <span v-else>{{ value }}</span>
        </template>
    </v-data-table>
</template>

<script setup lang="ts">

import {computed, onMounted, ref, watch} from "vue";
import {api} from "@/api";
import {chain} from "lodash";
import {DatasetPageDTO, TransformationResultMessageDTO} from "@/generated-sources";
import {$vfm} from "vue-final-modal";
import DiffToolModal from "@/views/main/project/modals/DiffToolModal.vue";

const props = defineProps<{
    datasetId: string,
    deletedRows?: Array<number>,
    modifications?: Array<TransformationResultMessageDTO>
}>()

const rows = ref<DatasetPageDTO | null>(null);
const options = ref<{ page: number, itemsPerPage: number }>({page: 1, itemsPerPage: 10})

onMounted(async () => await getDatasetPage())

watch(() => options.value, async () => await getDatasetPage(), {deep: true})

async function getDatasetPage() {
    return rows.value = await api.getDatasetRows(props.datasetId, (options.value.page - 1) * options.value.itemsPerPage, options.value.itemsPerPage);
}

const headers = computed(
    () => chain(rows.value === null ? [] : Object.keys(rows.value.content[0]))
        .filter(v => v !== '_GISKARD_INDEX_')
        .map(column => ({
            text: column,
            value: column,
            cellClass: 'overflow-ellipsis'
        }))
        .sortBy('text')
        .value()
)

function rowClasses(item) {
    return props.deletedRows?.includes(item['_GISKARD_INDEX_']) ? 'deleted-row' : '';
}

const modificationsMap = computed(() => chain(props.modifications ?? [])
    .keyBy('rowId')
    .mapValues('modifications')
    .value())

function openDiff(oldValue: string, newValue: string) {
    $vfm.show({
        component: DiffToolModal,
        bind: {
            oldValue,
            newValue
        }
    });
}
</script>

<style>
.deleted-row {
    background-color: #d6d8d9;
    color: #1b1e21;
    text-decoration: line-through;
}

.deleted-row:hover {
    background-color: #bfc2c4 !important;
    color: #151719;
}

td:has(div.modified-cell) {
    background-color: #d1ecf1;
    color: #0c5460;
    cursor: pointer;
}

tr:hover td:has(div.modified-cell) {
    background-color: #aedde6 !important;
    color: #062B32;
}
</style>
