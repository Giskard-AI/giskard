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
  let inputs = [];
  if (props.execution.inputs.length > 0) {
    inputs = props.execution.inputs;
  } else {
    // This is a bit hacky, but there is no other way because the test suite input list is never guaranteed to be present :(
    inputs.push({
      name: "model",
      type: "BaseModel",
      isAlias: false,
      value: result.inputs["model"],
      params: []
    });

    inputs.push({
      name: "dataset",
      type: "Dataset",
      isAlias: false,
      value: result.inputs["dataset"],
      params: []
    });

    // name: arg.name,
    // type: arg.type,
    // isAlias: false,
    // value: '',
    // params: []
  }

  let model = inputs.filter(i => i.name == "model")[0].value;

  let res = await api.runAdHocTest(testSuiteStore.projectId!, suiteTest.testUuid, inputs, true);
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

