<template>
  <div>
    <v-container fluid class='pa-0'>
      <v-row align="center">
        <v-col cols="6" :align="'right'" align-self="end" class="pl-0 pb-0">
          <v-container>
            <v-row>
              <v-col>
                <v-select
                    dense
                    :items="statusFilter" label="Status" v-model="status" hide-details></v-select>
              </v-col>
              <v-col cols="8" class="pl-0">
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
      <v-row>
        <v-col class="pt-0">
          <div class="body-1 text-subtitle-1">
            Total: {{ nbTotalTests }} tests.&nbsp; &nbsp; Executed: {{ nbTestsPassed + nbTestsFailed }}.&nbsp; &nbsp;
            Passed: {{ nbTestsPassed }}.&nbsp; &nbsp; Failed: {{ nbTestsFailed }}.
          </div>
        </v-col>
      </v-row>

      <v-row>
        <v-col>
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
        </v-col>
      </v-row>
    </v-container>
  </div>
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
  @Prop({required: true}) suiteId!: number;

  tests: { [id: number]: TestDTO } = {};
  filteredTests: { [id: number]: TestDTO } = {};
  isTestSuiteRunning = false;
  runningTestIds = new Set();
  search: string = "";
  nbTestsPassed: number = 0;
  nbTestsFailed: number = 0;
  nbTotalTests: number = 0;
  statusFilter = ['All', 'Passed', 'Failed', 'Not Executed']
  status = 'All'


  @Watch("search")
  @Watch("status")
  private filterTests() {
    let search = this.search;
    let status = this.status;
    this.filteredTests = Object.fromEntries(
        Object.entries(this.tests)
            .filter(function (test) {
              let filterStatus: boolean;
              switch (status) {
                case 'Passed':
                  filterStatus = test[1].status == TestResult.PASSED
                  break;
                case 'Failed':
                  filterStatus = test[1].status == TestResult.FAILED
                  break;
                case 'Not Executed':
                  filterStatus = test[1].status == null
                  break;
                default:
                  filterStatus = true;
              }

              let name = test[1].name;
              let filterName = name.toLocaleLowerCase().includes(search.toLocaleLowerCase());

              return filterName && filterStatus;
            })
    )
    this.getAllNumbersTests()
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
      this.getAllNumbersTests();
    }
  }

  private setNumbersTests(result?: TestResult) {
    return Object.values(this.filteredTests)
        .filter((test) => result != null ? test.status == result : true)
        .reduce((partial) => partial + 1, 0);
  }

  private getAllNumbersTests() {
    this.nbTestsPassed = this.setNumbersTests(TestResult.PASSED);
    this.nbTestsFailed = this.setNumbersTests(TestResult.FAILED);
    this.nbTotalTests = this.setNumbersTests();
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
    this.getAllNumbersTests();
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