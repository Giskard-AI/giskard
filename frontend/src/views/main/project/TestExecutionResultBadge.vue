<template>
  <div>
    <v-alert
        border='left'
        type='error'
        v-if="result.status === 'ERROR'">
      {{ result.message }}
    </v-alert>
    <template v-for='testResult in result.result'>
      <v-alert
        tile
        class='test-results'
        :color='getBadgeColor(result.status)'
        :type='TEST_RESULT_DATA[result.status].type'
        dismissible
        close-icon='mdi-close'
      >
        <div class='d-flex justify-space-between align-center'>
          <div class='text-h6'>Test {{ result.status.toLowerCase() }}</div>
          <div class='text-body-2'>{{ result.executionDate | date }}</div>
        </div>
        <div class='d-flex justify-space-between align-center'>
          <div class='text-body-2'>Metric: {{ testResult.result.metric }}</div>
          <div class='text-body-2 text-right'
               v-if='testResult.result.messages && testResult.result.messages.length'>
            {{ testResult.result.messages[0].text }}
          </div>
          <!--              <a class="text-body-2 results-link text-decoration-underline">Full results</a>-->
        </div>
      </v-alert>
    </template>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import { TestResult, TestTemplateExecutionResultDTO } from '@/generated-sources';
import { testStatusToColor } from '@/views/main/tests/test-utils';
import { Prop } from 'vue-property-decorator';
import Component from 'vue-class-component';
import { TEST_RESULT_DATA } from '@/utils/tests.utils';

@Component({
  computed: {
    TEST_RESULT_DATA() {
      return TEST_RESULT_DATA;
    }
  }
})
export default class TestExecutionResultBadge extends Vue {
  @Prop({ required: true }) result!: TestTemplateExecutionResultDTO;

  getBadgeColor(testStatus: TestResult) {
    return testStatusToColor(testStatus);
  }

}
</script>

<style scoped lang="scss">

</style>
