<template>
  <div class='d-flex w100 align-start'>
    <v-alert :color='testResultStyle.color' :icon='testResultStyle.icon' class='flex-grow-1' prominent
             text>
      <v-row align='center'>
        <v-col class='grow d-flex flex-wrap'>
          <h4 v-if='!props.execution' class='text-alert'>
            No execution has been performed yet!
          </h4>
          <h4 v-else-if='props.execution.result === TestResult.ERROR' class='text-alert'>
            An error occurred during the execution. Executed <strong>{{
              timeSince(execution.executionDate)
            }}</strong>
          </h4>
          <h4 v-else class='text-alert'>Test suite
            {{ props.execution.result === TestResult.PASSED ? 'passed' : 'failed' }}:
            <span v-if='successRatio.error > 0'>{{ plurialize('test', successRatio.error) }} with error</span>
            <span
              v-if='successRatio.error > 0 && (successRatio.passed > 0 || successRatio.failed > 0)'>, </span>
            <span v-if='successRatio.failed > 0'>{{
                plurialize('test', successRatio.failed)
              }} failed</span>
            <span v-if='successRatio.failed > 0 && successRatio.passed > 0'>, </span>
            <span v-if='successRatio.passed > 0'>{{
                plurialize('test', successRatio.passed)
              }} passed</span>
            <span
              v-if='successRatio.failed > 0 || successRatio.passed > 0 || successRatio.error > 0'>. </span>
            <span>Executed {{ timeSince(execution.executionDate) }}</span>
          </h4>
          <v-spacer />
          <v-btn v-if='props.execution' :color="props.execution.result === TestResult.PASSED ? 'primary' : 'error'"
                 small
                 @click='openLogs'>execution logs
          </v-btn>
        </v-col>
      </v-row>
    </v-alert>
  </div>
</template>

<script lang='ts' setup>

import { SuiteTestDTO, SuiteTestExecutionDTO, TestResult, TestSuiteExecutionDTO } from '@/generated-sources';
import { computed } from 'vue';
import { $vfm } from 'vue-final-modal';
import ExecutionLogsModal from '@/views/main/project/modals/ExecutionLogsModal.vue';
import { storeToRefs } from 'pinia';
import { useTestSuiteStore } from '@/stores/test-suite';
import { plurialize } from '@/utils/string.utils';
import { Colors } from '@/utils/colors';
import { timeSince } from '@/utils/time.utils';
import mixpanel from 'mixpanel-browser';

const props = defineProps<{
  tests: {
    suiteTest: SuiteTestDTO
    result?: SuiteTestExecutionDTO
  }[],
  execution?: TestSuiteExecutionDTO,
  compact: boolean,
  tryMode: boolean
}>();

const { suite, projectId } = storeToRefs(useTestSuiteStore());

const testResultStyle = computed(() => {
  if (!props.execution) {
    return {
      icon: 'block',
      color: 'dark-grey'
    };
  }
  switch (props.execution.result) {
    case TestResult.PASSED:
      return {
        icon: 'done',
        color: Colors.PASS
      };
    case TestResult.FAILED:
      return {
        icon: 'close',
        color: Colors.FAIL
      };
    default:
      return {
        icon: 'error',
        color: Colors.FAIL
      };
  }
});

const successRatio = computed(() => ({
  passed: executedTests.value.filter(({ result }) => result!.status === TestResult.PASSED).length,
  failed: executedTests.value.filter(({ result }) => result!.status === TestResult.FAILED).length,
  error: executedTests.value.filter(({ result }) => result!.status === TestResult.ERROR).length
}));

const executedTests = computed(() => !props.execution || props.execution.result === TestResult.ERROR ? []
  : props.tests.filter(({ result }) => result !== undefined));

function openLogs() {
  $vfm.show({
    component: ExecutionLogsModal,
    bind: {
      logs: props.execution?.logs
    }
  });

  mixpanel.track('Open test suite execution logs', {
    suiteId: suite.value!.id,
    projectId: projectId.value!,
    suiteExecutionStatus: props.execution?.result
  });

}
</script>

<style lang='scss' scoped>
.clickable {
  cursor: pointer;
  text-decoration: underline;
}

.text-alert {
  font-style: normal;
  font-weight: 500;
  font-size: 1em;
  line-height: 24px;
  letter-spacing: 0.005em;
  font-feature-settings: 'liga' off;
}
</style>

