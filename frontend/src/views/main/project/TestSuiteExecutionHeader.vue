<template>
  <div class="d-flex w100">
    <v-icon
        :color="!props.execution ? 'grey' : props.execution.result === TestResult.PASSED ? Colors.PASS : Colors.FAIL"
        size="64">{{
        testResultIcon
      }}
    </v-icon>
    <div>
      <h2>

        Test Suite
      </h2>
      <h4
          v-if="!props.execution">No execution has been performed yet!</h4>
      <h4
          v-else-if="props.execution.result === TestResult.ERROR">An error arose during the execution</h4>
      <h4 v-else-if="tests.length === 0">No test match the current filter</h4>
      <h4 v-else-if="executedTests.length > 0" :style="{
          color: successColor
        } ">Success ratio: {{ successRatio.passed }} /
        {{ successRatio.executed }}</h4>
    </div>
    <div class="flex-grow-1"/>
    <v-btn icon @click="openLogs" color="secondary">
      <v-icon>text_snippet</v-icon>
    </v-btn>
    <v-btn icon @click="openSettings" color="secondary" v-if="!compact">
      <v-icon>settings</v-icon>
    </v-btn>
  </div>
</template>

<script setup lang="ts">

import {
  SuiteTestDTO,
  SuiteTestExecutionDTO,
  TestFunctionDTO,
  TestResult,
  TestSuiteExecutionDTO
} from '@/generated-sources';
import {computed} from 'vue';
import {Colors, pickHexLinear, rgbToHex, SUCCESS_GRADIENT} from '@/utils/colors';
import {api} from '@/api';
import {$vfm} from 'vue-final-modal';
import CreateTestSuiteModal from '@/views/main/project/modals/CreateTestSuiteModal.vue';
import ExecutionLogsModal from '@/views/main/project/modals/ExecutionLogsModal.vue';
import {storeToRefs} from 'pinia';
import {useTestSuiteStore} from '@/stores/test-suite';

const props = defineProps<{
  tests: {
    suiteTest: SuiteTestDTO,
    test: TestFunctionDTO,
    result?: SuiteTestExecutionDTO
  }[],
  execution?: TestSuiteExecutionDTO,
  compact: boolean
}>();

const {suite, projectId} = storeToRefs(useTestSuiteStore());


const testResultIcon = computed(() => {
  if (!props.execution) {
    return 'block'
  }
  switch (props.execution.result) {
    case TestResult.PASSED:
      return 'done';
    case TestResult.FAILED:
      return 'close';
    default:
      return 'error';
  }
})

const executedTests = computed(() => !props.execution || props.execution.result === TestResult.ERROR ? []
    : props.tests.filter(({result}) => result !== undefined));


const successRatio = computed(() => ({
  passed: executedTests.value.filter(({result}) => result!.passed).length,
  executed: executedTests.value.length
}))

const successColor = computed(() => successRatio.value.executed === 0 ? Colors.PASS :
    rgbToHex(pickHexLinear(SUCCESS_GRADIENT, successRatio.value.passed / successRatio.value.executed)));

async function openSettings() {
  const project = await api.getProject(projectId.value!)
  $vfm.show({
    component: CreateTestSuiteModal,
    bind: {
      projectKey: project.key,
      projectId: project.id,
      suite: suite.value
    }
  });
}

function openLogs() {
  $vfm.show({
    component: ExecutionLogsModal,
    bind: {
      logs: props.execution?.logs
    }
  });
}
</script>

