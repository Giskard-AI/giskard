<template>
  <div class="d-flex">
    <div class="timeline" v-for="execution in [...executions].reverse()">
      <v-tooltip bottom>
        <template v-slot:activator="{ on, attrs }">
          <v-btn
              :color="execution.testResult.passed ? Colors.PASS : Colors.FAIL"
              icon
              v-bind="attrs"
              v-on="on"
              @click="showExecution(execution.testSuiteResult)"
          >
            <v-icon>circle</v-icon>
          </v-btn>
        </template>
        <span>{{ execution.testSuiteResult.executionDate | date }}</span>
      </v-tooltip>
    </div>
  </div>

</template>

<script setup lang="ts">

import {SuiteTestExecutionDTO, TestSuiteExecutionDTO} from '@/generated-sources';
import {useRouter} from 'vue-router/composables';
import {Colors} from '@/utils/colors';

const {executions} = defineProps<{
  executions: {
    testResult: SuiteTestExecutionDTO,
    testSuiteResult: TestSuiteExecutionDTO
  }[]
}>();

const router = useRouter();

function showExecution(execution: TestSuiteExecutionDTO) {
  router.push({
    name: 'test-suite-execution', params: {
      suiteId: execution.suiteId.toString(10),
      executionId: execution.id.toString(10)
    }
  })
}

</script>

<style scoped lang="scss">
.timeline {
  position: relative;

  // Draw a line between previous and current element
  &:not(:last-child):before {
    content: "";
    display: block;
    width: 100%;
    height: 3px;
    background: #000;
    right: -50%;
    top: calc(50% - 1px);
    position: absolute;
  }

}
</style>
