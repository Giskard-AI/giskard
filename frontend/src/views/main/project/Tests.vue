<template>
  <div>
    <v-container fluid>
      <v-row>
        <v-col :align="'right'">
          <v-btn small tile color="primary" class="mx-1" @click="createTestSuite()">
            <v-icon left>add</v-icon>
            create test
          </v-btn>
        </v-col>
      </v-row>

      <v-row>
        <v-col>

          <v-list two-line class="tests-list">
            <template v-for="(item, index) in items">
              <v-divider :inset="false"></v-divider>

              <v-list-item :key="item.title" v-ripple class="test-list-item" @click="openTest(item.id)">
                <v-list-item-avatar>
                  <v-icon color="green lighten-2">circle</v-icon>
                </v-list-item-avatar>
                <v-list-item-content>
                  <v-list-item-title v-html="item.name"></v-list-item-title>
                  <v-list-item-subtitle>
                    <span class="font-weight-regular">Last executed</span>:
                    <UseTimeAgo v-slot="{ timeAgo }" :time="new Date(2022, 2, parseInt(Math.random()*22))">
                      {{ timeAgo }}
                    </UseTimeAgo>

                  </v-list-item-subtitle>
                </v-list-item-content>
                <v-spacer/>
                <v-btn tile small @click="runTest($event, item.id)" z-index="9999999">
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
import {UseTimeAgo} from "@vueuse/components";

@Component({
  components: {TestSuiteCreateModal, UseTimeAgo}
})
export default class Tests extends Vue {
  @Prop({required: true}) suiteId!: number;

  tests: Array<ITest> = []
  selectedItem = 1;

  items = [
    {
      name: 'Metamorphic invariance 1',
      id: 1,
    },
    {
      name: 'Metamorphic invariance 2',
      id: 2,
    },
    {
      name: 'Metamorphic invariance 3',
      id: 3,
    },
    {
      name: 'Metamorphic invariance 4',
      id: 4,
    },
    {
      name: 'Metamorphic invariance 5',
      id: 5,
    },
  ];


  public openTestSuite(suite) {
    this.$router.push({name: 'suite-details', params: {suiteId: suite.id}})
  }

  public async createTestSuite() {
    // const newTestSuite = await this.$dialog.showAndWait(TestSuiteCreateModal, {width: 800, projectId: this.projectId});
    // debugger
    // await this.$router.push({
    //   name: 'suite-details', params: {
    //     projectId: this.projectId.toString(),
    //     suiteId: newTestSuite.id
    //   }
    // });
  }

  public async mounted() {
    this.tests = (await api.getTests(this.suiteId)).data;
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