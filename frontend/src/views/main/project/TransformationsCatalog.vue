<template>
    <div class="vc mt-2 pb-0" v-if="transformationFunctions.length > 0">
        <div class="vc">
            <v-container class="main-container vc">
                <v-alert
                    v-if="!hasGiskardFilters"
                    color="warning"
                    border="left"
                    outlined
                    colored-border
                    icon="warning"
                >
                    <span>Giskard filters are not available.</span>
                    <StartWorkerInstructions/>
                </v-alert>
                <v-row class="fill-height">
                    <v-col cols="4" class="vc fill-height">
                        <v-text-field label="Search filter" append-icon="search" outlined
                                      v-model="searchFilter"></v-text-field>
                        <v-list three-line>
                            <v-list-item-group v-model="selected" color="primary" mandatory>
                                <template v-for="filter in filteredTestFunctions">
                                    <v-divider/>
                                    <v-list-item :value="filter">
                                        <v-list-item-content>
                                            <v-list-item-title class="test-title">
                                                <div class="d-flex align-center">
                                                    {{ filter.name }}
                                                    <v-spacer class="flex-grow-1"/>
                                                    <v-tooltip bottom v-if="filter.potentiallyUnavailable">
                                                        <template v-slot:activator="{ on, attrs }">
                                                            <div v-bind="attrs" v-on="on">
                                                                <v-icon color="orange">warning</v-icon>
                                                            </div>
                                                        </template>
                                                        <span>This filter is potentially unavailable. Start your external ML worker to display available filters.</span>
                                                    </v-tooltip>
                                                </div>
                                            </v-list-item-title>
                                            <v-list-item-subtitle v-if="filter.tags">
                                                <v-chip class="mr-2" v-for="tag in sorted(filter.tags)" x-small
                                                        :color="pasterColor(tag)">
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
                            <v-alert
                                v-if="selected.potentiallyUnavailable"
                                color="warning"
                                border="left"
                                outlined
                                colored-border
                                icon="warning"
                            >
                                <span>This filter is potentially unavailable. Start your external ML worker to display available filters.</span>
                                <pre></pre>
                                <StartWorkerInstructions/>
                            </v-alert>
                            <pre class="test-doc caption pt-5">{{ selected.doc }}</pre>
                            <div class="pt-5">
                                <div class="d-flex justify-space-between">
                                    <span class="text-h6">Inputs</span>
                                    <v-btn width="100" small tile outlined @click="tryMode = !tryMode">{{
                                            tryMode ? 'Cancel' : 'Try it'
                                        }}
                                    </v-btn>
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
                                                <DatasetSelector v-if="tryMode" :project-id="projectId"
                                                                 label="Dataset"
                                                                 :return-object="false"
                                                                 :value.sync="selectedDataset"/>
                                            </v-col>
                                        </v-row>
                                    </v-list-item>
                                </v-list>
                                <v-row v-show="tryMode">
                                    <v-col :align="'right'">
                                        <v-btn width="100" small tile outlined class="primary" color="white"
                                               @click="runSlicingFunction">
                                            Run
                                        </v-btn>
                                    </v-col>
                                </v-row>
                                <v-row v-if="transformationResult">
                                    <v-col>
                                        <span class="text-h6">Result</span>
                                        <p>Modified rows: {{ transformationResult.modifiedRow }} /
                                            {{ transformationResult.totalRow }}</p>
                                        <template>
                                            <v-data-table
                                                :headers="headers"
                                                :items="resultData"
                                                hide-default-footer
                                                class="elevation-1"
                                            ></v-data-table>
                                        </template>
                                    </v-col>
                                </v-row>
                                <v-row>
                                    <v-col>
                                        <v-expansion-panels flat @change="resizeEditor">
                                            <v-expansion-panel>
                                                <v-expansion-panel-header class="pa-0">Code</v-expansion-panel-header>
                                                <v-expansion-panel-content class="pa-0">
                                                    <MonacoEditor
                                                        ref="editor"
                                                        v-model='selected.code'
                                                        class='editor'
                                                        language='python'
                                                        style="height: 300px; min-height: 300px"
                                                        :options="monacoOptions"
                                                    />
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
        <h1 class="pt-16">You haven't started any ML worker yet!</h1>
        <StartWorkerInstructions/>
    </v-container>
</template>

<script setup lang="ts">
import _, {chain} from "lodash";
import {computed, inject, onActivated, ref} from "vue";
import {pasterColor} from "@/utils";
import MonacoEditor from 'vue-monaco';
import {editor} from "monaco-editor";
import {TransformationFunctionDTO, TransformationResultDTO} from "@/generated-sources";
import StartWorkerInstructions from "@/components/StartWorkerInstructions.vue";
import {storeToRefs} from "pinia";
import {useCatalogStore} from "@/stores/catalog";
import DatasetSelector from "@/views/main/utils/DatasetSelector.vue";
import {api} from "@/api";
import IEditorOptions = editor.IEditorOptions;

const l = MonacoEditor;
let props = defineProps<{
    projectId: number,
    suiteId?: number
}>();

const editor = ref(null)

const searchFilter = ref<string>("");
let {transformationFunctions} = storeToRefs(useCatalogStore());
const selected = ref<TransformationFunctionDTO | null>(null);
const transformationResult = ref<TransformationResultDTO | null>(null);
const tryMode = ref<boolean>(false);
const selectedDataset = ref<string | null>(null);

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
        .value();
})

onActivated(async () => {
    if (transformationFunctions.value.length > 0) {
        selected.value = transformationFunctions.value[0];
    }
});

async function runSlicingFunction() {
    transformationResult.value = await api.runAdHocTransformationFunction(selected.value!.uuid, selectedDataset.value!);
}

const infoHeader = {
    text: '',
    value: 'info'
}
const infoColumns = ['count', 'unique', 'top', 'freq']

const headers = computed(() =>
    [
        infoHeader,
        ...chain(transformationResult.value?.describeColumns ?? [])
            .map(column => ({
                text: column.columnName,
                value: column.columnName,
                cellClass: 'overflow-ellipsis'
            }))
            .value()
    ]
);

const resultData = computed(() => chain(infoColumns)
    .map(info => ({
        info,
        ...chain(transformationResult.value?.describeColumns ?? [])
            .keyBy('columnName')
            .mapValues(info)
            .value()
    }))
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
    flex: 1; /* formerly flex: 1 0 auto; */
    background: green;
    padding: 5px;
    margin: 5px;
    min-height: 0; /* new */
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
