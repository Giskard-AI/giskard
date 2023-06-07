<template>
    <div class="d-flex flex-column gap-16">
        <v-alert v-if="props.tests.length === 0" type="info" text>No test match the current filter</v-alert>
        <SuiteTestExecutionCard v-for="({result, suiteTest}) in props.tests" :suite-test="suiteTest"
                                :result="result" :compact="compact" :is-past-execution="isPastExecution"/>
    </div>
</template>

<script setup lang="ts">

import {storeToRefs} from 'pinia';
import {useTestSuiteStore} from '@/stores/test-suite';
import {SuiteTestDTO, SuiteTestExecutionDTO} from '@/generated-sources';
import SuiteTestExecutionCard from "@/views/main/project/SuiteTestExecutionCard.vue";

const props = withDefaults(defineProps<{
    tests: {
        suiteTest: SuiteTestDTO,
        result?: SuiteTestExecutionDTO
    }[],
    compact: boolean,
    isPastExecution: boolean
}>(), {
    compact: false,
    isPastExecution: false
});

const testSuiteStore = useTestSuiteStore();
const {suite} = storeToRefs(testSuiteStore);
</script>

<style scoped lang="scss">
.gap-16 {
    gap: 16px;
}
</style>

