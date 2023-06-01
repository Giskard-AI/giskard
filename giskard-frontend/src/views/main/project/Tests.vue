<template>
  <v-container class="vertical-container overflow-x-hidden pl-0 pr-0" fluid>
    <v-row align="center">
      <v-col cols="6" :align="'right'" align-self="end" class="pl-0 pb-0">
        <v-container>
          <v-row>
            <v-col class="pr-0">
              <v-select
                  dense
                  :items="Object.entries(statusFilter)"
                  label="Status"
                  v-model="status"
                  hide-details
                  item-value="[1]"
                  item-text="[0]"
              ></v-select>
            </v-col>
            <v-col cols="8">
              <v-text-field
                  dense
                  hide-details
                  v-model="search"
                  append-icon="mdi-magnify"
                  label="Search"
              ></v-text-field>
            </v-col>
          </v-row>
        </v-container>
      </v-col>
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
    <v-row class="mt-0 counters text-body-2">
      <v-col>
        Total: {{ nbTotalTests }} tests.&nbsp; &nbsp; Executed: {{ nbTestsExecuted }}.&nbsp; &nbsp;
        Passed: {{ nbTestsPassed }}.&nbsp; &nbsp; Failed: {{ nbTestsFailed }}.
      </v-col>
    </v-row>

    <div class="vertical-container mt-5">
      <div>
        <v-list two-line class='tests-list'>
          <template v-for='(test) in filteredTests'>
            <v-divider :inset='false'></v-divider>

            <v-list-item :key='test.id' v-ripple class='test-list-item' @click='openTest(test.id)'>
              <v-list-item-avatar>
                <v-icon :color='testStatusToColor(test.status)'>{{ testStatusToIcon(test.status) }}</v-icon>
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
              <v-spacer/>
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
      </div>
    </div>
  </v-container>
</template>

<script lang='ts'>

import {Prop, Vue, Watch} from 'vue-property-decorator';
import Component from 'vue-class-component';
import TestSuiteCreateModal from '@/views/main/project/modals/TestSuiteCreateModal.vue';
import {api} from '@/api';
import TestCreateModal from '@/views/main/project/modals/TestCreateModal.vue';
import {TestDTO, TestExecutionResultDTO, TestResult} from '@/generated-sources';
import mixpanel from "mixpanel-browser";
import {testStatusToColor, testStatusToIcon} from "@/views/main/tests/test-utils";

@Component({
  components: {TestSuiteCreateModal, TestCreateModal}
})


export default class Tests extends Vue {
  private static EMPTY_TEST_STATUS_FILTER = 'All';
  @Prop({required: true}) suiteId!: number;

  tests: { [id: number]: TestDTO } = {};
  filteredTests: { [id: number]: TestDTO } = {};
  isTestSuiteRunning = false;
  runningTestIds = new Set();
  search: string = "";
  statusFilter = {
    'All': Tests.EMPTY_TEST_STATUS_FILTER,
    'Passed': TestResult.PASSED,
    'Failed': TestResult.FAILED,
    'Not Executed': null
  }
  status: string = Tests.EMPTY_TEST_STATUS_FILTER;


  @Watch("search")
  @Watch("status")
  private filterTests() {
    let search = this.search;
    let selectedStatus = this.status;
    this.filteredTests = Object.fromEntries(
        Object.entries(this.tests)
            .filter(function (test) {
              let filterStatus = selectedStatus === Tests.EMPTY_TEST_STATUS_FILTER || selectedStatus == test[1].status;

              let name = test[1].name;
              let filterName = name.toLocaleLowerCase().includes(search.toLocaleLowerCase());

              return filterName && filterStatus;
            })
    )
  }

  testStatusToColor(status: TestResult) {
    return testStatusToColor(status);
  }

  testStatusToIcon(status: TestResult) {
    return testStatusToIcon(status);
  }

  public isTestRunning(testId: number) {
    return this.runningTestIds.has(testId);
  }

  public async executeTestSuite() {
    this.isTestSuiteRunning = true;
    try {
      mixpanel.track('Run test suite', {suiteId: this.suiteId});
      let res = await api.executeTestSuite(this.suiteId);
      res.forEach((testResult: TestExecutionResultDTO) => {
        Tests.applyTestExecutionResults(this.tests[testResult.testId], testResult);
      });
    } finally {
      this.isTestSuiteRunning = false;
    }
  }

  private countTestsWithStatus(result?: TestResult | null) {
    return Object.values(this.filteredTests)
        .filter((test) => test.status == result)
        .length;
  }

  get nbTestsPassed() {
    return this.countTestsWithStatus(TestResult.PASSED);
  }

  get nbTestsFailed() {
    return this.countTestsWithStatus(TestResult.FAILED);
  }

  get nbTestsExecuted() {
    return this.nbTotalTests - this.countTestsWithStatus(null);
  }

  get nbTotalTests() {
    return Object.keys(this.filteredTests).length;
  }

  public async createTest() {
    const newTest = await this.$dialog.showAndWait(TestCreateModal, {width: 800, suiteId: this.suiteId});
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
    this.tests = Object.assign({}, ...testsList.map((x) => ({[x.id]: x})));
    this.filteredTests = this.tests;
  }

  public async mounted() {
    await this.init();
  }

  public async runTest(event: Event, test: TestDTO) {
    mixpanel.track('Run test from suite page', {testId: test.id});
    event.stopPropagation();
    this.runningTestIds.add(test.id);
    this.$forceUpdate();
    try {
      let runResult = await api.runTest(test.id);
      Tests.applyTestExecutionResults(test, runResult);
    } finally {
      this.runningTestIds.delete(test.id);
      this.$forceUpdate();
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
    this.$router.push({name: 'test-editor', params: {testId: testId.toString()}});
  }
}
</script>
<style scoped lang='scss'>
@import "src/styles/colors.scss";

.counters {
  color: $grey;
}

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