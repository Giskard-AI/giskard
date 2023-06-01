<template>
    <div class="d-flex flex-column">
        <SuiteTestExecutionCard v-for="({result, suiteTest}) in props.tests" :suite-test="suiteTest" :result="result"/>
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
    compact: boolean
}>(), {
    compact: false
});

const testSuiteStore = useTestSuiteStore();
const {suite} = storeToRefs(testSuiteStore);
</script>

