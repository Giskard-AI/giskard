<template>
    <LoadingFullscreen v-if="suite === null" name="suite"/>
    <v-container class="main-container vc" v-else-if="hasTest">
        <div class="d-flex">
        </div>
        <TestSuiteExecutionHeader :execution="execution" :tests="filteredTest" :compact="false"/>
        <SuiteTestExecutionList :tests="filteredTest" :compact="false" :is-past-execution="isPastExecution"/>
    </v-container>
    <v-container v-else class="d-flex flex-column vc fill-height">
        <v-alert class="text-center transparent">
            <p class="headline font-weight-medium grey--text text--darken-2">No tests have been added to the suite.</p>
        </v-alert>
        <v-btn tile color="primaryLight" class="primaryLightBtn" :to="{ name: 'project-catalog-tests', query: { suiteId: suite?.id } }">
            <v-icon left>add</v-icon>
            Add test
        </v-btn>
    </v-container>
</template>

<script setup lang="ts">

import {storeToRefs} from 'pinia';
import {useTestSuiteStore} from '@/stores/test-suite';
import {TestSuiteExecutionDTO} from '@/generated-sources';
import {computed, onMounted, watch} from 'vue';
import {chain} from 'lodash';
import {useTestSuiteCompareStore} from '@/stores/test-suite-compare';
import SuiteTestExecutionList from '@/views/main/project/SuiteTestExecutionList.vue';
import TestSuiteExecutionHeader from '@/views/main/project/TestSuiteExecutionHeader.vue';
import LoadingFullscreen from "@/components/LoadingFullscreen.vue";
import {TestsUtils} from "@/utils/tests.utils";

const props = withDefaults(defineProps<{
    execution?: TestSuiteExecutionDTO,
    isPastExecution: boolean,
    tryMode?: boolean
}>(), {
    tryMode: false
});

const testSuiteStore = useTestSuiteStore();
const {models, datasets, inputs, suite, projectId, hasTest, statusFilter, searchFilter} = storeToRefs(testSuiteStore);
const testSuiteCompareStore = useTestSuiteCompareStore();

onMounted(() => {
  testSuiteCompareStore.setCurrentExecution(props.execution ? props.execution.id : null);
})

watch(() => props.execution,
    () => testSuiteCompareStore.setCurrentExecution(props.execution ? props.execution.id : null),
    {deep: true});



const filteredTest = computed(() => suite.value === null ? [] : chain(suite.value!.tests)
    .map(suiteTest => ({
      suiteTest,
      result: props.execution?.results?.find(result => result.test.id === suiteTest.id)
    }))
    .filter(TestsUtils.statusFilter(statusFilter.value))
    .filter(TestsUtils.searchFilter(searchFilter.value))
    .value()
);
</script>

<style scoped lang="scss">
.log-viewer {
  overflow: auto;
  max-height: 400px;
}
</style>

