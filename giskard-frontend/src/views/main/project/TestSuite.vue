<template>
  <v-container fluid v-if="testSuite">
    <v-row>
      <v-col>
        <span>Test suite: </span>
        <router-link class="text-h6 text-decoration-none" :to="{name: 'suite-details', params: {
          suiteId: this.suiteId
         } }">
          {{ testSuite.name }}
        </router-link>
      </v-col>
      <v-col :align="'right'">
        <v-btn
            class="mx-2 mr-0"
            dark
            small
            outlined
            color="primary"
            @click="openSettings()"
        >
          <v-icon>settings</v-icon>
        </v-btn>
        <v-btn
            class="mx-2 mr-0"
            dark
            small
            outlined
            color="primary"
            @click="remove()"
        >
          <v-icon>delete</v-icon>
        </v-btn>
      </v-col>
    </v-row>
    <router-view></router-view>
  </v-container>
</template>

<script lang="ts">
import Vue from "vue";
import Component from "vue-class-component";
import {Prop} from "vue-property-decorator";
import {api} from "@/api";
import ModelSelector from "@/views/main/utils/ModelSelector.vue";
import DatasetSelector from "@/views/main/utils/DatasetSelector.vue";
import * as _ from "lodash";
import Tests from "@/views/main/project/Tests.vue";
import TestSuiteSettings from "@/views/main/project/modals/TestSuiteSettings.vue";
import {TestSuiteDTO} from '@/generated-sources';


@Component({
  components:
      {
        DatasetSelector, ModelSelector,
        Tests, TestSuiteSettings
      }
})
export default class TestSuite extends Vue {
  @Prop({required: true}) projectId?: number;
  @Prop({required: true}) suiteId!: number;
  testSuite: TestSuiteDTO | null = null;
  savedTestSuite: TestSuiteDTO | null = null;

  async activated() {
    await this.init();
  }

  async mounted() {
    await this.init();
  }


  private async init() {
    this.savedTestSuite = await api.getTestSuite(this.suiteId);
    this.testSuite = _.cloneDeep(this.savedTestSuite);
  }

  async remove() {
    if (await this.$dialog.confirm({
      text: `Would you like to delete test suite "${this.testSuite?.name}"?`,
      title: 'Delete test suite',
      showClose: false,
      actions: {
        false: 'Cancel',
        true: 'Delete'
      }
    })) {
      await api.deleteTestSuite(this.testSuite!.id);
      await this.$router.push({name: 'project-test-suites', params: {projectId: this.projectId!.toString()}})
    }
  }

  async openSettings() {
    let modifiedSuite = await this.$dialog.showAndWait(TestSuiteSettings, {width: 800, testSuite: this.testSuite});
    if (modifiedSuite) {
      this.testSuite = modifiedSuite;
    }
  }
}
</script>

<style scoped>

</style>