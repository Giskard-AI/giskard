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
import {SuiteTestDTO, SuiteTestExecutionDTO, TestFunctionDTO, TestSuiteExecutionDTO} from '@/generated-sources';
import {Colors} from '@/utils/colors';
import {$vfm} from 'vue-final-modal';
import SuiteTestInfoModal from '@/views/main/project/modals/SuiteTestInfoModal.vue';
import {api} from '@/api';
import ConfirmModal from "@/views/main/project/modals/ConfirmModal.vue";
import SuiteTestExecutionCard from "@/views/main/project/SuiteTestExecutionCard.vue";
import {useRouter} from "vue-router/composables";

const props = withDefaults(defineProps<{
    tests: {
        suiteTest: SuiteTestDTO,
        result?: SuiteTestExecutionDTO
    }[],
    compact: boolean,
    isPastExecution: boolean,
  execution: TestSuiteExecutionDTO
}>(), {
    compact: false,
    isPastExecution: false
});

const testSuiteStore = useTestSuiteStore();
const {suite} = storeToRefs(testSuiteStore);

async function debugTest(result: SuiteTestExecutionDTO, suiteTest: SuiteTestDTO) {

  let model = props.execution.inputs.filter(input => input.name === 'model')[0].value;

  let res = await api.runAdHocTest(testSuiteStore.projectId!, suiteTest.testUuid, props.execution.inputs, true);

  let dataset = res.result[0].result.outputDfUuid;

  const debuggingSession = await api.prepareInspection({
    datasetId: dataset,
    modelId: model as string,
    name: "Debugging session ..."
  });

  await router.push({
    name: 'inspection',
    params: {
      projectId: testSuiteStore.projectId!,
      inspectionId: debuggingSession.id
    }
  });
}
</script>

<style scoped lang="scss">
.gap-16 {
    gap: 16px;
}
</style>

