<template>
  <div>
    <v-container fluid>
      <v-row>
        <v-col :align="'right'">
          <v-btn small tile color="primary" class="mx-1" @click="createTestSuite()">
            <v-icon left>add</v-icon>
            create test suite
          </v-btn>
        </v-col>
      </v-row>
      <v-data-table
          class="row-pointer"
          :items="testSuites"
          :headers="tableHeaders"
          @click:row="openTestSuite"
      >
      </v-data-table>
    </v-container>
  </div>
</template>

<script lang="ts">

import {IProjectFile, ITestSuite} from "@/interfaces";
import {Prop, Vue} from "vue-property-decorator";
import Component from "vue-class-component";
import TestSuiteCreateModal from "@/views/main/project/modals/TestSuiteCreateModal.vue";
import {api} from "@/api";

@Component({
  components: {TestSuiteCreateModal}
})
export default class TestSuites extends Vue {
  @Prop({required: true}) projectId!: number;

  testSuites: Array<ITestSuite> = []

  private getProjectFileName(obj: IProjectFile) {
    return obj ? (obj.name || obj.filename) : "";
  }

  get tableHeaders() {
    return [
      {
        text: "Name",
        sortable: true,
        value: "name",
        align: "left"
      },
      {
        text: "Model",
        sortable: true,
        value: "model.name",
        align: "left"
      },
      {
        text: "Train dataset",
        sortable: true,
        value: "trainDataset.name",
        align: "left"
      },
      {
        text: "Test dataset",
        sortable: true,
        value: "testDataset.name",
        align: "left"
      }
    ];
  }

  public openTestSuite(suite) {
    this.$router.push({name: 'suite-details', params: {suiteId: suite.id}})
  }

  public async createTestSuite() {
    const newTestSuite = await this.$dialog.showAndWait(TestSuiteCreateModal, {width: 800, projectId: this.projectId});
    await this.$router.push({
      name: 'suite-details', params: {
        projectId: this.projectId.toString(),
        suiteId: newTestSuite.id
      }
    });
  }

  public async activated() {
    await this.init();
  }

  public async mounted() {
    await this.init();
  }

  private async init() {
    this.testSuites = (await api.getTestSuites(this.projectId)).data.map((ts: ITestSuite) => {
      ts.model.name = this.getProjectFileName(ts.model);
      ts.trainDataset.name = this.getProjectFileName(ts.trainDataset);
      ts.testDataset.name = this.getProjectFileName(ts.testDataset);
      return ts;
    });
  }
}
</script>