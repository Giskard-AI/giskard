<template>
  <v-container fluid v-if="testDetails">
    <v-row v-if="testDetails">
      <v-col :cols="4">
        <span>Test: </span><span class="text-h6">{{ testDetails.name }}</span>
      </v-col>
      <v-col :align="'right'">
        <v-select
            hide-details
            dense
            clearable label="Test function" :items="testEditorConfig.functions"
            @change="selectTestPreset"
            item-text="name" return-object></v-select>
      </v-col>
      <v-col :align="'right'" :cols="1">
        <v-btn tile color="primary"
               :disabled="!isDirty()"
               @click="save()">
          <v-icon dense left>save</v-icon>
          Save
        </v-btn>
      </v-col>
    </v-row>
    <v-row>
      <v-col :cols="4">
        <v-alert
            text
            style="opacity: 80%"
            color="blue"
            outlined
            type="info"
        >
          <p class="font-weight-bold text-center">Available variables</p>
          <table style="width: 100%">
            <tr>
              <td><code>clf_predict</code></td>
              <td>Model function</td>
            </tr>
            <tr>
              <td><code>test_df</code></td>
              <td>Test dataframe</td>
            </tr>
            <tr>
              <td><code>train_df</code></td>
              <td>Train dataframe</td>
            </tr>
          </table>
          <div class="mt-4 mb-0">
            <p class="ma-0">These variables will be provided at the test execution time</p>
            <p class="ma-0">you can reference them in the custom test script</p>
          </div>
        </v-alert>

      </v-col>
      <v-col :cols="8">
        <MonacoEditor
            v-if="testDetails.type === 'CODE'"
            v-model="testDetails.code"
            class="editor"
            height="500"
            language="python"
            :options="$root.monacoOptions"
        />
      </v-col>
    </v-row>
    <v-row>
      <v-col :align="'right'">
        <v-btn tile
               @click="runTest()"
               :loading="executingTest"
               :disabled="executingTest"

        >
          <v-icon>arrow_right</v-icon>
          <span>Run</span>
        </v-btn>
      </v-col>
    </v-row>
    <v-row v-if="runResult">
      <v-col>
        <v-alert
            v-model="showRunResult"
            dismissible
            border="left"
            type="error"
            v-if="runResult.status === 'ERROR'">
          <pre>{{ runResult.message }}</pre>
        </v-alert>
        <template v-for="testResult in runResult.result">
          <v-alert
              v-if="runResult.status === 'SUCCESS'"
              v-model="showRunResult"
              type="success"
              color="green"
              outlined
              dismissible
          >
            <div class="text-h6">Test results: {{ testResult.name }}</div>
            <table style="width: 100%; text-align: center">
              <tr>
                <th>Total rows tested</th>
                <th>Failed rows</th>
                <th>Failed rows (%)</th>
              </tr>
              <tr>
                <td>{{ testResult.result.elementCount }}</td>
                <td>{{ testResult.result.unexpectedCount }}</td>
                <td>{{ testResult.result.unexpectedPercent | formatNumber }}</td>
              </tr>
            </table>

            <!--          <pre>{{runResult}}</pre>-->
          </v-alert>
        </template>
      </v-col>
    </v-row>
    <!--    <v-row>-->
    <!--      <v-col>-->
    <!--        <pre>{{ testDetails }}</pre>-->
    <!--      </v-col>-->
    <!--    </v-row>-->
  </v-container>
</template>

<script lang="ts">
import Vue from "vue";
/* tslint:disable-next-line */
import MonacoEditor from 'vue-monaco'

import Component from "vue-class-component";
import {Prop} from "vue-property-decorator";
import {api} from "@/api";
import {ITest, ITestExecutionResult} from "@/interfaces";
import _ from "lodash";
import numeral from "numeral";


type ITestFunction = {
  id: string;
  code: string;
  name: string;
  type: 'CODE'
};

interface IEditorConfig {
  functions: ITestFunction[]
}

Vue.filter("formatNumber", function (value) {
  return numeral(value).format("0.0"); // displaying other groupings/separators is possible, look at the docs
});

@Component({components: {MonacoEditor}})
export default class TestEditor extends Vue {
  @Prop({required: true}) testId!: number;
  testDetails: ITest | null = null;
  testDetailsOriginal: ITest | null = null;
  testEditorConfig: IEditorConfig | null = null;
  testFunction: ITestFunction | null = null;
  showRunResult: boolean = false;
  runResult: ITestExecutionResult | null = null;
  executingTest = false;

  async mounted() {
    await this.init();
  }

  isDirty() {
    return !_.isEqual(this.testDetailsOriginal, this.testDetails);
  }

  async save() {
    this.testDetailsOriginal = (await api.saveTest(this.testDetails!)).data;
  }

  async selectTestPreset(selectedTest: ITestFunction) {
    if (selectedTest.type === 'CODE') {

      if (_.isEqual(this.testDetailsOriginal?.code, this.testDetails?.code) || await this.$dialog.confirm({
        text: `Test code changes will be discarded. Would you like to continue?`,
        title: 'Change test code'
      })) {
        this.testDetails!.code = selectedTest.code;
      }

    }
  }

  async runTest() {
    try {
      this.executingTest = true;

      this.resetTestResults();

      if (this.isDirty()) {
        await this.save();
      }
      this.runResult = (await api.runTest(this.testId)).data;
    } finally {
      this.executingTest = false;
    }

  }

  private resetTestResults() {
    this.showRunResult = true;
    this.runResult = null;
  }

  private async init() {
    this.testDetails = (await api.getTestDetails(this.testId)).data;

    this.testDetailsOriginal = _.cloneDeep(this.testDetails);

    this.testEditorConfig = {
      functions: [{
        id: "test_metamorphic_invariance",
        name: "Metamorphic Invariance",
        type: "CODE",
        // language=Python
        /* tslint:disable-next-line */
        code: `
          perturbation = {"YOUR_FEATURE": lambda x: x}
          population = test_df

          test_metamorphic_invariance(
            df=test_df,
            model_fn=clf_predict,
            perturbation_dict=perturbation,
            filter=population)

        `
      }],


    }
    // this.testEditorConfig = (await api.getTestEditorConfig()).data;
  }
}
</script>

<style scoped>
.editor {
  height: 500px;
  border: 1px solid grey;
}
</style>