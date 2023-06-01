<template>
    <LoadingFullscreen v-if="suite === null" name="suite"/>
    <v-container class="main-container vc" v-else-if="hasTest">
        <div class="d-flex">

        </div>
        <TestSuiteExecutionHeader :execution="execution" :tests="filteredTest" :compact="false"/>
        <SuiteTestExecutionList :tests="filteredTest" :compact="false"/>
    </v-container>
    <v-container v-else class="d-flex flex-column vc fill-height">
        <v-alert class="text-center">
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
import {statusFilterOptions, useTestSuiteStore} from '@/stores/test-suite';
import {TestSuiteExecutionDTO} from '@/generated-sources';
import {computed, onMounted, watch} from 'vue';
import {chain} from 'lodash';
import {useTestSuiteCompareStore} from '@/stores/test-suite-compare';
import SuiteTestExecutionList from '@/views/main/project/SuiteTestExecutionList.vue';
import TestSuiteExecutionHeader from '@/views/main/project/TestSuiteExecutionHeader.vue';
import LoadingFullscreen from "@/components/LoadingFullscreen.vue";

const props = defineProps<{ execution?: TestSuiteExecutionDTO }>();

const testSuiteStore = useTestSuiteStore();
const {models, datasets, inputs, suite, projectId, hasTest, statusFilter, searchFilter} = storeToRefs(testSuiteStore);
const testSuiteCompareStore = useTestSuiteCompareStore();

onMounted(() => {
    testSuiteCompareStore.setCurrentExecution(props.execution ? props.execution.id : null);
})

watch(() => props.execution,
    () => testSuiteCompareStore.setCurrentExecution(props.execution ? props.execution.id : null),
    { deep: true });



const filteredTest = computed(() => suite.value === null ? [] : chain(suite.value!.tests)
    .map(suiteTest => ({
        suiteTest,
        result: props.execution?.results?.find(result => result.test.id === suiteTest.id)
    }))
    .filter(({ result }) => statusFilterOptions.find(opt => statusFilter.value === opt.label)!.filter(result))
    .filter(({ suiteTest }) => {
        const test = suiteTest.test;

        const keywords = searchFilter.value.split(' ')
            .map(keyword => keyword.trim().toLowerCase())
            .filter(keyword => keyword !== '');
        return keywords.filter(keyword =>
            test.name.toLowerCase().includes(keyword)
            || test.doc?.toLowerCase()?.includes(keyword)
            || test.displayName?.toLowerCase()?.includes(keyword)
            || test.tags?.filter(tag => tag.includes(keyword))?.length > 0
        ).length === keywords.length;
    })
    .value()
);
</script>

<style scoped lang="scss">
.log-viewer {
    overflow: auto;
    max-height: 400px;
}
</style>

