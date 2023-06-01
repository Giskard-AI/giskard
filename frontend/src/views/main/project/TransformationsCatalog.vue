<template>
    <div class="vc mt-2 pb-0" v-if="transformationFunctions.length > 0">
        <div class="vc">
            <v-container class="main-container vc">
                <v-alert v-if="!hasGiskardFilters" color="warning" border="left" outlined colored-border icon="warning">
                    <span>Giskard filters are not available.</span>
                    <StartWorkerInstructions />
                </v-alert>
                <v-row class="fill-height">
                    <v-col cols="4" class="vc fill-height">
                        <v-text-field label="Search filter" append-icon="search" outlined v-model="searchFilter"></v-text-field>
                        <v-list three-line class="vc fill-height">
                            <v-list-item-group v-model="selected" color="primary" mandatory>
                                <template v-for="transformationFunction in filteredTestFunctions">
                                    <v-divider />
                                    <v-list-item :value="transformationFunction">
                                        <v-list-item-content>
                                            <v-list-item-title class="test-title">
                                                <div class="d-flex align-center">
                                                    {{
                                                        transformationFunction.displayName ?? transformationFunction.name
                                                    }}
                                                    <v-spacer class="flex-grow-1" />
                                                    <v-tooltip bottom v-if="transformationFunction.potentiallyUnavailable">
                                                        <template v-slot:activator="{ on, attrs }">
                                                            <div v-bind="attrs" v-on="on">
                                                                <v-icon color="orange">warning</v-icon>
                                                            </div>
                                                        </template>
                                                        <span>This filter is potentially unavailable. Start your external ML worker to display available filters.</span>
                                                    </v-tooltip>
                                                </div>
                                            </v-list-item-title>
                                            <v-list-item-subtitle v-if="transformationFunction.tags">
                                                <v-chip class="mr-2" v-for="tag in sorted(transformationFunction.tags)" x-small :color="pasterColor(tag)">
                                                    {{ tag }}
                                                </v-chip>
                                            </v-list-item-subtitle>
                                        </v-list-item-content>
                                    </v-list-item>
                                </template>
                            </v-list-item-group>
                        </v-list>
                    </v-col>
                    <v-col cols="8" v-if="selected" class="vc fill-height">
                        <span class="text-h5">{{ selected.displayName ?? selected.name }}</span>
                        <div class="vc overflow-x-hidden pr-5">
                            <v-alert v-if="selected.potentiallyUnavailable" color="warning" border="left" outlined colored-border icon="warning">
                                <span>This filter is potentially unavailable. Start your external ML worker to display available filters.</span>
                                <pre></pre>
                                <StartWorkerInstructions />
                            </v-alert>
                            <pre class="test-doc caption pt-5">{{ selected.doc }}</pre>
                            <div class="pt-5">
                                <div class="d-flex justify-space-between">
                                    <span class="text-h6">Inputs</span>
                                </div>
                                <v-list>
                                    <v-list-item class="pl-0 pr-0">
                                        <v-row>
                                            <v-col>
                                                <v-list-item-content>
                                                    <v-list-item-title>Dataset</v-list-item-title>
                                                    <v-list-item-subtitle class="text-caption">
                                                        BaseDataset
                                                    </v-list-item-subtitle>
                                                </v-list-item-content>
                                            </v-col>
                                            <v-col>
                                                <DatasetSelector :project-id="projectId" label="Dataset" :return-object="false" :value.sync="selectedDataset" />
                                            </v-col>
                                        </v-row>
                                    </v-list-item>
                                    <v-list-item class="pl-0 pr-0">
                                        <v-row v-if="selected.cellLevel">
                                            <v-col>
                                                <v-list-item-content>
                                                    <v-list-item-title>Column</v-list-item-title>
                                                    <v-list-item-subtitle class="text-caption">
                                                        str
                                                    </v-list-item-subtitle>
                                                </v-list-item-content>
                                            </v-col>
                                            <v-col>
                                                <DatasetColumnSelector :project-id="projectId" :dataset="selectedDataset" :column-type="selected.columnType" :value.sync="selectedColumn" />
                                            </v-col>
                                        </v-row>
                                    </v-list-item>
                                </v-list>
                                <SuiteInputListSelector :editing="true" :model-value="transformationArguments" :inputs="inputType" :project-id="props.projectId" />
                                <v-row>
                                    <v-col :align="'right'">
                                        <v-btn width="100" small tile outlined class="primary" color="white" @click="runSlicingFunction">
                                            Run
                                        </v-btn>
                                    </v-col>
                                </v-row>
                                <v-row v-if="transformationResult">
                                    <v-col>
                                        <span class="text-h6">Result</span>
                                        <p>Modified rows:
                                            {{
                                                transformationResult.modifications.length
                                            }} /
                                            {{
                                                transformationResult.totalRows
                                            }}</p>
                                        <DatasetTable :dataset-id="transformationResult.datasetId" :modifications="transformationResult.modifications" />
                                    </v-col>
                                </v-row>
                                <v-row>
                                    <v-col>
                                        <v-expansion-panels flat @change="resizeEditor">
                                            <v-expansion-panel>
                                                <v-expansion-panel-header class="grey lighten-5 pl-6 pr-4 py-2">Code</v-expansion-panel-header>
                                                <v-divider></v-divider>
                                                <v-expansion-panel-content class="pl-0 pr-1">
                                                    <MonacoEditor ref="editor" v-model='selected.code' class='editor' language='python' style="height: 300px; min-height: 300px" :options="monacoOptions" />
                                                </v-expansion-panel-content>
                                            </v-expansion-panel>
                                        </v-expansion-panels>
                                    </v-col>
                                </v-row>
                            </div>
                        </div>

                    </v-col>
                </v-row>
            </v-container>
        </div>
    </div>
    <v-container v-else class="d-flex flex-column vc fill-height">
        <h1 class="pt-16">ML Worker is not connected</h1>
        <StartWorkerInstructions />
    </v-container>
</template>

<script setup lang="ts">
import _, { chain } from "lodash";
import { computed, inject, onActivated, ref, watch } from "vue";
import { pasterColor } from "@/utils";
import MonacoEditor from 'vue-monaco';
import { editor } from "monaco-editor";
import { FunctionInputDTO, TransformationFunctionDTO } from "@/generated-sources";
import StartWorkerInstructions from "@/components/StartWorkerInstructions.vue";
import { storeToRefs } from "pinia";
import { useCatalogStore } from "@/stores/catalog";
import DatasetSelector from "@/views/main/utils/DatasetSelector.vue";
import { api } from "@/api";
import DatasetTable from "@/components/DatasetTable.vue";
import SuiteInputListSelector from "@/components/SuiteInputListSelector.vue";
import DatasetColumnSelector from "@/views/main/utils/DatasetColumnSelector.vue";
import IEditorOptions = editor.IEditorOptions;

const l = MonacoEditor;
let props = defineProps<{
    projectId: number,
    suiteId?: number
}>();

const editor = ref(null)

const searchFilter = ref<string>("");
let { transformationFunctions } = storeToRefs(useCatalogStore());
const selected = ref<TransformationFunctionDTO | null>(null);
const transformationResult = ref<FunctionInputDTO | null>(null);
const selectedDataset = ref<string | null>(null);
const selectedColumn = ref<string | null>(null);
let transformationArguments = ref<{ [name: string]: FunctionInputDTO }>({})

const monacoOptions: IEditorOptions = inject('monacoOptions');
monacoOptions.readOnly = true;

function resizeEditor() {
    setTimeout(() => {
        editor.value.editor.layout();
    })
}

function sorted(arr: any[]) {
    const res = _.cloneDeep(arr);
    res.sort()
    return res;
}

const hasGiskardFilters = computed(() => {
    return transformationFunctions.value.find(t => t.tags.includes('giskard')) !== undefined
})

const filteredTestFunctions = computed(() => {
    return chain(transformationFunctions.value)
        .filter((func) => {
            const keywords = searchFilter.value.split(' ')
                .map(keyword => keyword.trim().toLowerCase())
                .filter(keyword => keyword !== '');

            return keywords.filter(keyword =>
                func.name.toLowerCase().includes(keyword)
                || func.doc?.toLowerCase()?.includes(keyword)
                || func.displayName?.toLowerCase()?.includes(keyword)
            ).length === keywords.length;
        })
        .sortBy(t => t.displayName ?? t.name)
        .value();
})

onActivated(async () => {
    if (transformationFunctions.value.length > 0) {
        selected.value = transformationFunctions.value[0];
    }
});

async function runSlicingFunction() {
    const params = Object.values(transformationArguments.value);
    if (selected.value!.cellLevel) {
        params.push({
            isAlias: false,
            name: 'column_name',
            params: [],
            type: 'str',
            value: selectedColumn.value
        })
    }

    transformationResult.value = await api.datasetProcessing(props.projectId, selectedDataset.value!, [{
        uuid: selected.value!.uuid,
        params,
        type: 'TRANSFORMATION'
    }]);
}

watch(() => selected.value, () => {
    transformationResult.value = null;

    if (!selected.value) {
        return;
    }

    transformationArguments.value = chain(selected.value.args)
        .keyBy('name')
        .mapValues(arg => ({
            name: arg.name,
            isAlias: false,
            type: arg.type,
            value: null
        }))
        .value()
})

const inputType = computed(() => chain(selected.value?.args ?? [])
    .keyBy('name')
    .mapValues('type')
    .value()
);

</script>

<style scoped lang="scss">
.main-container {
    width: 100%;
    max-width: 100%;
}

.test-title {
    white-space: break-spaces;
}

.box-grow {
    flex: 1;
    /* formerly flex: 1 0 auto; */
    background: green;
    padding: 5px;
    margin: 5px;
    min-height: 0;
    /* new */
}

::v-deep .v-expansion-panel-content__wrap {
    padding: 0;
}

.test-doc {
    white-space: break-spaces;
}

::v-deep .overflow-ellipsis {
    max-width: 200px;
    text-overflow: ellipsis;
    overflow: hidden;
    white-space: nowrap;
}
</style>
