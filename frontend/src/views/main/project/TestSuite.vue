<template>
    <div class="vc mt-2 pb-0 parent-container">
        <div class="vc">
            <v-container class="main-container vc">
                <div class="d-flex pl-3 pr-3">
                    <h1 class="test-suite-name">{{ suite.name }}</h1>
                    <div class="flex-grow-1"/>
                    <v-btn tile class='mx-1' v-if="hasTest"
                           :to="{ name: 'project-catalog-tests', query: { suiteId: suiteId } }" color="secondary">
                        <v-icon>add</v-icon>
                        Add test
                    </v-btn>
                </div>
                <v-tabs class="pl-3 pr-3">
                    <v-tab :to="{ name: 'test-suite-overview' }">
                        <v-icon>mdi-chart-bar</v-icon>
                        Report
                    </v-tab>
                    <v-tab :to="{ name: 'test-suite-executions' }">
                        <v-icon>history</v-icon>
                        Past executions
                    </v-tab>
                    <v-tab disabled>
                        <v-icon>settings</v-icon>
                        Configuration
                    </v-tab>
                </v-tabs>
                <v-row class="mt-0 overview-container pl-3 pr-3">
                    <v-col>
                        <div class="d-flex align-center">
                            <div v-if="hasTest && route.name === 'test-suite-overview'"
                                 :to="{ name: 'test-suite-executions' }">
                          <span>
                              <b>{{ suite.tests.length }}</b>
                              test{{ suite.tests.length > 1 ? 's' : '' }} | </span>
                                <span v-if="latestExecution">
                              Latest execution <b>{{ timeSince(latestExecution.executionDate) }}</b>
                          </span>
                                <span v-else>Never executed</span>
                            </div>
                            <div class="flex-grow-1"/>
                            <v-btn tile class='mx-1' v-if="hasTest && hasInput" @click='openRunTestSuite(true)'
                                   color="secondary">
                                <v-icon>compare</v-icon>
                                Compare
                            </v-btn>
                            <v-btn tile class='mx-1' v-if="hasTest" @click='() => openRunTestSuite(false)'
                                   color="primary">
                                <v-icon>arrow_right</v-icon>
                                Run test suite
                            </v-btn>
                        </div>
                    </v-col>
                </v-row>
                <v-row class="vc overview-container pl-3 pr-3">
                    <v-col class="vc" cols="12">
                        <router-view/>
                    </v-col>
                </v-row>
            </v-container>
    </div>
  </div>
</template>

<script lang="ts" setup>

import {computed, onActivated, watch} from "vue";
import {useMainStore} from "@/stores/main";
import {useTestSuiteStore} from '@/stores/test-suite';
import {storeToRefs} from 'pinia';
import {useRoute, useRouter} from 'vue-router/composables';
import {$vfm} from 'vue-final-modal';
import RunTestSuiteModal from '@/views/main/project/modals/RunTestSuiteModal.vue';
import {useCatalogStore} from "@/stores/catalog";
import {timeSince} from "../../../utils/time.utils";

const props = defineProps<{
    projectId: number,
    suiteId: number
}>();

const mainStore = useMainStore();
const {suite, inputs, executions, hasTest, hasInput} = storeToRefs(useTestSuiteStore())

onActivated(() => loadData());
watch(() => props.suiteId, () => loadData());

const {loadTestSuites, runTestSuite} = useTestSuiteStore();
const {loadCatalog} = useCatalogStore();

const router = useRouter();
const route = useRoute();

const latestExecution = computed(() => executions.value.length === 0 ? null : executions.value[0]);

async function loadData() {
    await loadTestSuites(props.projectId, props.suiteId);
    await loadCatalog(props.projectId);
}

async function openRunTestSuite(compareMode: boolean) {
    if (hasInput.value) {
        await $vfm.show({
            component: RunTestSuiteModal,
            bind: {
                projectId: props.projectId,
                suiteId: props.suiteId,
                inputs: inputs.value,
                compareMode,
                previousParams: executions.value.length === 0 ? {} : executions.value[0].inputs
            }
        });
    } else {
        await runTestSuite([]);
    }
}


</script>


<style scoped lang="scss">
.main-container {
    width: 100%;
    max-width: 100%;
    color: rgb(98, 98, 98);

    b {
        color: black;
    }
}

.parent-container {
    margin-left: -12px;
    margin-right: -12px;
}

.overview-container {
    background-color: #f5f5f5;
}

.test-suite-name {
    color: rgb(32, 57, 48);
}
</style>
