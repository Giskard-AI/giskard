<template>
  <v-card v-if="testSuite && modifiedTestSuite" tile>
    <v-card-title>
      Test suite settings
    </v-card-title>
    <v-card-text>
      <v-form>
        <v-text-field
            outlined
            class="flex-1 ma-0"
            v-model="modifiedTestSuite.name"
            label="Name"
        ></v-text-field>
        <ModelSelector :value.sync="modifiedTestSuite.model" :project-id="testSuite.projectId"/>
        <DatasetSelector
            :value.sync="modifiedTestSuite.trainDataset" :project-id="testSuite.projectId"
            label="Train dataset"
        />
        <DatasetSelector
            :value.sync="modifiedTestSuite.testDataset" :project-id="testSuite.projectId"
            label="Test dataset"
        />
      </v-form>
    </v-card-text>
    <v-card-actions>
      <v-spacer/>
      <v-btn tile color="primary"
             :disabled="!isDirty()"
             @click="save()">
        <v-icon dense left>save</v-icon>
        Save
      </v-btn>
    </v-card-actions>
  </v-card>

</template>

<script lang="ts">
import Vue from "vue";
import Component from "vue-class-component";
import DatasetSelector from "@/views/main/utils/DatasetSelector.vue";
import ModelSelector from "@/views/main/utils/ModelSelector.vue";
import {Prop} from "vue-property-decorator";
import {ITestSuite} from "@/interfaces";
import * as _ from "lodash";
import {api} from "@/api";

@Component({
  components:
      {
        DatasetSelector, ModelSelector,
      }
})

export default class TestSuiteSettings extends Vue {
  @Prop({required: true}) testSuite!: ITestSuite;
  modifiedTestSuite: ITestSuite | null = null;

  isDirty() {
    return !_.isEqual(this.modifiedTestSuite, this.testSuite);
  }

  async save() {
    if (this.testSuite && this.modifiedTestSuite) {
      this.modifiedTestSuite = (await api.saveTestSuite(this.modifiedTestSuite)).data;
      this.$emit('submit', this.modifiedTestSuite)
    }
  }

  mounted() {
    this.modifiedTestSuite = _.cloneDeep(this.testSuite);
  }
}
</script>

<style scoped>

</style>