<template>
  <div>
    <v-container fluid>
      <v-row>
        <v-col :align="'right'">
          <v-btn small tile color="primary" class="mx-1" @click="createTest()">
            <v-icon left>add</v-icon>
            create test
          </v-btn>
        </v-col>
      </v-row>

      <v-row>
        <v-col>

          <v-list two-line class="tests-list">
            <template v-for="(test, index) in tests">
              <v-divider :inset="false"></v-divider>

              <v-list-item :key="test.name" v-ripple class="test-list-item" @click="openTest(test.id)">
                <v-list-item-avatar>
                  <v-icon color="green lighten-2">circle</v-icon>
                </v-list-item-avatar>
                <v-list-item-content>
                  <v-list-item-title v-html="test.name"></v-list-item-title>
                  <v-list-item-subtitle>
                    <span class="font-weight-regular">Last executed</span>:
<!--                    <UseTimeAgo v-slot="{ timeAgo }" :time="new Date(2022, 2, parseInt(Math.random()*22))">-->
<!--                      {{ timeAgo }}-->
<!--                    </UseTimeAgo>-->

                  </v-list-item-subtitle>
                </v-list-item-content>
                <v-spacer/>
                <v-btn tile small @click="runTest($event, test.id)">
                  <v-icon>arrow_right</v-icon>
                  <span>Run</span>
                </v-btn>
              </v-list-item>

            </template>
            <v-divider :inset="false"></v-divider>

            <!--          </v-list-item-group>-->
          </v-list>
        </v-col>

      </v-row><!--      <v-data-table-->
      <!--          class="row-pointer"-->
      <!--          :items="testSuites"-->
      <!--          :headers="tableHeaders"-->
      <!--          @click:row="openTestSuite"-->
      <!--      >-->
      <!--      </v-data-table>-->
    </v-container>
  </div>
</template>

<script lang="ts">

import {ITest} from "@/interfaces";
import {Prop, Vue} from "vue-property-decorator";
import Component from "vue-class-component";
import TestSuiteCreateModal from "@/views/main/project/modals/TestSuiteCreateModal.vue";
import {api} from "@/api";
// import {UseTimeAgo} from "@vueuse/components";
import TestCreateModal from "@/views/main/project/modals/TestCreateModal.vue";

@Component({
  components: {TestSuiteCreateModal, TestCreateModal}
})
export default class Tests extends Vue {
  @Prop({required: true}) suiteId!: number;

  tests: Array<ITest> = []
  selectedItem = 1;

  public openTestSuite(suite) {
    this.$router.push({name: 'suite-details', params: {suiteId: suite.id}})
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
  private async init(){
    this.tests = (await api.getTests(this.suiteId)).data;
  }
  public async mounted() {
    await this.init();
  }

  public async runTest(event: Event, testId: number) {
    event.stopPropagation();
    let runResult = (await api.runTest(testId)).data;
    console.log('RUN', runResult);
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
<style scoped lang="scss">
@import "/src/styles/colors.scss";

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