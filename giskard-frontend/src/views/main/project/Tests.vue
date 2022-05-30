<template>
  <div>
    <v-container fluid class='pa-0'>
      <v-row>
        <v-col :align="'right'">
          <v-btn small tile color='primary' class='mx-1' @click='createTest()'>
            <v-icon left>add</v-icon>
            create test
          </v-btn>
          <v-btn small tile class='mx-1' @click='executeTestSuite()'
                 :loading='isTestSuiteRunning'
                 :disabled='isTestSuiteRunning'>
            <v-icon>arrow_right</v-icon>
            run all
          </v-btn>
        </v-col>
      </v-row>

      <v-row>
        <v-col>
          <v-list two-line class='tests-list'>
            <template v-for='(test) in tests'>
              <v-divider :inset='false'></v-divider>

              <v-list-item :key='test.id' v-ripple class='test-list-item' @click='openTest(test.id)'>
                <v-list-item-avatar>
                  <v-icon :color='testStatusToColor(test.status)'>circle</v-icon>
                </v-list-item-avatar>
                <v-list-item-content>
                  <v-list-item-title v-text='test.name'></v-list-item-title>
                  <v-list-item-subtitle v-if='test.lastExecutionDate'>
                    <span class='font-weight-regular'>Last executed</span>:
                    <span :title="test.lastExecutionDate | moment('dddd, MMMM Do YYYY, h:mm:ss a')">{{
                        test.lastExecutionDate | moment('from')
                      }}</span>
                  </v-list-item-subtitle>
                </v-list-item-content>
                <v-spacer />
                <v-btn tile small @click='runTest($event, test)'
                       :disabled='isTestSuiteRunning || isTestRunning(test.id)'
                       :loading='isTestRunning(test.id)'
                >
                  <v-icon>arrow_right</v-icon>
                  <span>Run</span>
                </v-btn>
              </v-list-item>

            </template>
            <v-divider :inset='false'></v-divider>
          </v-list>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script lang='ts'>

import { Prop, Vue } from 'vue-property-decorator';
import Component from 'vue-class-component';
import TestSuiteCreateModal from '@/views/main/project/modals/TestSuiteCreateModal.vue';
import { api } from '@/api';
import TestCreateModal from '@/views/main/project/modals/TestCreateModal.vue';
import { TestDTO, TestExecutionResultDTO, TestResult } from '@/generated-sources';

@Component({
  components: { TestSuiteCreateModal, TestCreateModal }
})
export default class Tests extends Vue {
  @Prop({ required: true }) suiteId!: number;

  tests: { [id: number]: TestDTO } = {};
  isTestSuiteRunning = false;
  runningTestIds = new Set();

  testStatusToColor(status: TestResult) {
    switch (status) {
      case TestResult.PASSED:
        return 'green lighten-2';
      case TestResult.FAILED:
        return 'orange lighten-2';
      case TestResult.ERROR:
        return 'red lighten-2';
      default:
        return 'grey lighten-2';
    }
  }

  public isTestRunning(testId: number) {
    return this.runningTestIds.has(testId);
  }

  public async executeTestSuite() {
    this.isTestSuiteRunning = true;
    try {

      let res = await api.executeTestSuite(this.suiteId);
      res.forEach((testResult: TestExecutionResultDTO) => {
        Tests.applyTestExecutionResults(this.tests[testResult.testId], testResult);
      });
    } finally {
      this.isTestSuiteRunning = false;
    }
  }


  public async createTest() {
    const newTest = await this.$dialog.showAndWait(TestCreateModal, { width: 800, suiteId: this.suiteId });
    await this.$router.push({
      name: 'test-editor', params: {
        testId: newTest.id
      }
    });
  }

  async activated() {
    await this.init();
  }

  private async init() {
    let testsList = await api.getTests(this.suiteId);
    this.tests = Object.assign({}, ...testsList.map((x) => ({ [x.id]: x })));

  }

  public async mounted() {
    await this.init();
  }

  public async runTest(event: Event, test: TestDTO) {
    event.stopPropagation();
    this.runningTestIds.add(test.id);
    this.$forceUpdate();
    console.log('After added', this.runningTestIds);
    try {
      let runResult = await api.runTest(test.id);
      Tests.applyTestExecutionResults(test, runResult);
    } finally {
      this.runningTestIds.delete(test.id);
    }
  }

  private static applyTestExecutionResults(test: TestDTO, runResult: TestExecutionResultDTO) {
    test.lastExecutionDate = runResult.executionDate;
    test.status = runResult.status;
  }

  /**
   * navigate to test
   * do not use `:to` to be able to click on Run button
   * @param testId
   */
  public openTest(testId: number) {
    this.$router.push({ name: 'test-editor', params: { testId: testId.toString() } });
  }
}
</script>
<style scoped lang='scss'>
@import "src/styles/colors.scss";

.test-list-item {
  cursor: pointer;

  &:hover {
    background-color: $hover;
  }

  .tests-list {
    width: 100%;
  }

}
</style>