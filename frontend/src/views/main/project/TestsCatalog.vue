<template>
    <div class="vc mt-2 pb-0" v-if="testFunctions.length > 0">
        <div class="vc">
            <v-container class="main-container vc">
                <v-alert v-if="!hasGiskardTests" color="warning" border="left" outlined colored-border icon="warning">
                    <span>Giskard test are not available.</span>
                    <StartWorkerInstructions />
                </v-alert>
                <v-row class="fill-height">
                    <v-col cols="4" class="vc fill-height">
                        <v-text-field label="Search test" append-icon="search" outlined v-model="searchFilter"></v-text-field>
                        <v-list three-line class="vc fill-height">
                            <v-list-item-group v-model="selected" color="primary" mandatory>
                                <template v-for="test in filteredTestFunctions">
                                    <v-divider />
                                    <v-list-item :value="test">
                                        <v-list-item-content>
                                            <v-list-item-title class="test-title">
                                                <div class="d-flex align-center">
                                                    {{ test.displayName ?? test.name }}
                                                    <v-spacer class="flex-grow-1" />
                                                    <v-tooltip bottom v-if="test.potentiallyUnavailable">
                                                        <template v-slot:activator="{ on, attrs }">
                                                            <div v-bind="attrs" v-on="on">
                                                                <v-icon color="orange">warning</v-icon>
                                                            </div>
                                                        </template>
                                                        <span>This test is potentially unavailable. Start your external ML worker to display available tests.</span>
                                                    </v-tooltip>
                                                </div>
                                            </v-list-item-title>
                                            <v-list-item-subtitle v-if="test.tags">
                                                <v-chip class="mr-2" v-for="tag in sorted(test.tags)" x-small :color="pasterColor(tag)">
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
                        <div class="d-flex justify-space-between">
                            <span class="text-h5" id="test-name">{{ selected.displayName ?? selected.name }}</span>
                            <v-btn small tile color="primaryLight" class="primaryLightBtn" @click="addToTestSuite">
                                <v-icon dense class="pr-2">mdi-plus</v-icon>
                                Add to test suite
                            </v-btn>
                        </div>

                        <!-- <div class="d-flex justify-space-between">

                        </div> -->
                        <!--            <AddTestToTestSuiteModal style="border: 1px solid lightgrey"></AddTestToTestSuiteModal>-->
                        <div class="vc overflow-x-hidden pr-5">
                            <v-alert v-if="selected.potentiallyUnavailable" color="warning" border="left" outlined colored-border icon="warning">
                                <span>This test is potentially unavailable. Start your external ML worker to display available tests.</span>
                                <pre></pre>
                                <StartWorkerInstructions />
                            </v-alert>

                            <div id="description-group" class="mt-8 py-4">
                                <div class="description-group-title">
                                    <span class="group-title">Description</span>
                                    <v-icon right class="group-icon pb-1 ml-1">mdi-text-box</v-icon>
                                </div>
                                <p class="test-doc">{{ selected.doc }}</p>
                            </div>

                            <v-divider></v-divider>

                            <div id="inputs-group" class="py-4">
                                <div class="inputs-group-title">
                                    <span class="group-title">Inputs</span>
                                    <v-icon right class="group-icon pb-1 ml-1">mdi-pencil-box</v-icon>

                                </div>
                                <SuiteInputListSelector :editing="true" :model-value="testArguments" :inputs="inputType" :project-id="props.projectId" />
                                <v-row>
                                    <v-col :align="'right'">
                                        <v-btn width="100" small tile outlined class="primary" color="white" @click="runTest">
                                            Run
                                        </v-btn>
                                    </v-col>
                                </v-row>
                                <v-row style="height: 150px" v-if="testResult">
                                    <v-col>
                                        <TestExecutionResultBadge :result="testResult" />
                                    </v-col>
                                </v-row>

                            </div>

                            <v-divider></v-divider>


                            <div id="code-group" class="py-4">
                                <div class="inputs-group-title">
                                    <span class="group-title">Code</span>
                                    <v-icon right class="group-icon pb-1 ml-1">mdi-code-braces-box</v-icon>
                                </div>

                                <div class="d-flex flex-column mt-2">
                                    <span class="py-2">Test definition</span>
                                    <CodeSnippet :codeContent="selected.code"></CodeSnippet>
                                </div>

                                <div class="d-flex flex-column mt-4">
                                    <span class="py-2">Example usage</span>
                                    <CodeSnippet></CodeSnippet>
                                </div>
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
import { api } from "@/api";
import _, { chain } from "lodash";
import { computed, inject, onActivated, ref, watch } from "vue";
import { pasterColor } from "@/utils";
import MonacoEditor from 'vue-monaco';
import TestExecutionResultBadge from "@/views/main/project/TestExecutionResultBadge.vue";
import { editor } from "monaco-editor";
import { TestFunctionDTO, TestInputDTO, TestTemplateExecutionResultDTO } from "@/generated-sources";
import AddTestToSuite from '@/views/main/project/modals/AddTestToSuite.vue';
import { $vfm } from 'vue-final-modal';
import StartWorkerInstructions from "@/components/StartWorkerInstructions.vue";
import { storeToRefs } from "pinia";
import { useCatalogStore } from "@/stores/catalog";
import SuiteInputListSelector from "@/components/SuiteInputListSelector.vue";
import IEditorOptions = editor.IEditorOptions;
import CodeSnippet from "@/components/CodeSnippet.vue";

const l = MonacoEditor;
let props = defineProps<{
    projectId: number,
    suiteId?: number
}>();

const editor = ref(null)

const searchFilter = ref<string>("");
let { testFunctions } = storeToRefs(useCatalogStore());
let selected = ref<TestFunctionDTO | null>(null);
let testArguments = ref<{ [name: string]: TestInputDTO }>({})
let testResult = ref<TestTemplateExecutionResultDTO | null>(null);


const monacoOptions: IEditorOptions = inject('monacoOptions');
monacoOptions.readOnly = true;

async function runTest() {
    testResult.value = await api.runAdHocTest(props.projectId, selected.value!.uuid, Object.values(testArguments.value));
}


function resizeEditor() {
    setTimeout(() => {
        editor.value.editor.layout();
    })
}

watch(selected, (value) => {
    testResult.value = null;

    if (value === null || value === undefined) {
        return;
    }

    testArguments.value = chain(value.args)
        .keyBy('name')
        .mapValues(arg => ({
            name: arg.name,
            isAlias: false,
            type: arg.type,
            value: null
        }))
        .value()
});


function sorted(arr: any[]) {
    const res = _.cloneDeep(arr);
    res.sort()
    return res;
}

const hasGiskardTests = computed(() => {
    return testFunctions.value.find(t => t.tags.includes('giskard')) !== undefined
})

const filteredTestFunctions = computed(() => {
    return chain(testFunctions.value)
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
    if (testFunctions.value.length > 0) {
        selected.value = testFunctions.value[0];
    }
});

function addToTestSuite() {
    $vfm.show({
        component: AddTestToSuite,
        bind: {
            projectId: props.projectId,
            test: selected.value,
            suiteId: props.suiteId,
            testArguments: testArguments.value
        }
    });
}

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
    font-family: 'Roboto', sans-serif;
    white-space: break-spaces;
    font-size: 1rem;
    line-height: 1.5rem;
    opacity: 0.9;
}

.group-title {
    font-size: 1.2rem;
    font-weight: 500;
    line-height: 2rem;
    letter-spacing: normal;
}

.group-icon {
    color: rgba($color: #000000, $alpha: 0.7);
    font-size: 1.25rem;
}

#test-name {
    font-weight: 500;
}
</style>
