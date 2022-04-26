<template>
  <ValidationObserver v-slot='{ invalid }' v-if='testDetails'>

    <v-row v-if='testDetails'>
      <v-col :cols='3'>
        <span class='text-h6'>
    <ValidationProvider name='Test name' mode='eager' rules='required' v-slot='{errors}'>
              <v-text-field
                label='Test name'
                class='shrink'
                type='text'
                v-model='testDetails.name'
                :error-messages='errors'
              ></v-text-field>
    </ValidationProvider>
        </span>
      </v-col>
      <v-col :align="'right'">
        <v-btn
          class='mx-2 mr-0'
          dark
          small
          outlined
          color='primary'
          @click='remove()'
        >
          <v-icon>delete</v-icon>
        </v-btn>
      </v-col>
    </v-row>
    <v-row>
      <v-col :cols='3'>
        <v-alert
          text
          style='opacity: 80%'
          color='blue'
          outlined
          type='info'
        >
          <p class='font-weight-bold text-center'>Available variables</p>
          <table style='width: 100%'>
            <tr>
              <td><code>model</code></td>
              <td>Model Inspector</td>
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
          <div class='mt-4 mb-0'>
            <p class='ma-0'>These variables will be provided at the test execution time</p>
            <p class='ma-0'>you can reference them in the custom test script</p>
          </div>
        </v-alert>

      </v-col>
      <v-col :cols='6'>
        <MonacoEditor
          v-if="testDetails.type === 'CODE'"
          v-model='testDetails.code'
          class='editor'
          language='python'
          :options='$root.monacoOptions'
        />
      </v-col>
      <v-col :cols='3'>
        <v-list>
          <v-subheader>Code presets</v-subheader>

          <template v-for='snippet in codeSnippets'>
            <v-hover v-slot='{ hover }' class='snippet'>
              <v-list-item dense v-ripple class='no-user-select' @click='copyCodeFromSnippet(snippet.code)'>
                <v-list-item-icon>
                  <v-icon class='mirror' v-show='hover' dense>exit_to_app</v-icon>
                </v-list-item-icon>
                <v-list-item-content class='text-center'>
                  <v-list-item-title>{{ snippet.name }}</v-list-item-title>
                </v-list-item-content>
                <v-list-item-action>
                  <v-tooltip bottom>
                    <template v-slot:activator='{ on, attrs }'>
                      <v-icon color='grey lighten-1'
                              dense
                              v-bind='attrs'
                              v-on='on'>mdi-information
                      </v-icon>
                    </template>
                    <span>{{ snippet.hint }}</span>
                  </v-tooltip>
                </v-list-item-action>

              </v-list-item>
            </v-hover>

            <v-divider />
          </template>

        </v-list>
      </v-col>
    </v-row>
    <v-row>
      <v-col :align="'right'">
        <v-btn tile color='primary'
               class='mr-3'
               :disabled='!isDirty() || invalid'
               @click='save()'>
          <v-icon dense left>save</v-icon>
          Save
        </v-btn>
        <v-btn
          tile
          @click='runTest()'
          :loading='executingTest'
          :disabled='executingTest'
        >
          <v-icon>arrow_right</v-icon>
          <span>Run</span>
        </v-btn>
      </v-col>
    </v-row>
    <v-row v-if='runResult'>
      <v-col>
        <v-alert
          v-model='showRunResult'
          dismissible
          border='left'
          type='error'
          v-if="runResult.status === 'ERROR'">
          {{ runResult.message }}
        </v-alert>
        <template v-for='testResult in runResult.result'>
          <v-alert
            v-model='showRunResult'
            :type="testResult.result.passed ? 'success' : 'error'"
            outlined
            dismissible
          >
            <div class='text-h6'>Test results: {{ testResult.name }}</div>
            <table style='width: 100%; text-align: center'>
              <tr>
                <th>Total rows tested</th>
                <th>Failed rows</th>
                <th>Failed rows (%)</th>
                <th>Metric</th>
              </tr>
              <tr>
                <td>{{ testResult.result.elementCount }}</td>
                <td>{{ testResult.result.unexpectedCount }}</td>
                <td>{{ testResult.result.unexpectedPercent | formatNumber }}</td>
                <td>{{ testResult.result.metric | formatNumber('0.00000') }}</td>
              </tr>
            </table>
          </v-alert>
        </template>
      </v-col>
    </v-row>
  </ValidationObserver>
</template>

<script lang='ts'>
import Vue from 'vue';
// @ts-ignore
import MonacoEditor from 'vue-monaco';

import Component from 'vue-class-component';
import { Prop } from 'vue-property-decorator';
import { api } from '@/api';
import { IEditorConfig, ITest, ITestExecutionResult, ITestFunction } from '@/interfaces';
import _ from 'lodash';
import numeral from 'numeral';

Vue.filter('formatNumber', function(value, fmt) {
  return numeral(value).format(fmt || '0.0'); // displaying other groupings/separators is possible, look at the docs
});

@Component({ components: { MonacoEditor } })
export default class TestEditor extends Vue {
  @Prop({ required: true }) testId!: number;
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
    const t = this.testDetails;
    if (t) {
      this.testDetailsOriginal = (await api.saveTest({
        testSuite: t.testSuite,
        language: t.language,
        code: t.code,
        type: t.type,
        name: t.name,
        id: t.id
      })).data;
    }
  }

  async remove() {
    if (await this.$dialog.confirm({
      text: `Would you like to delete test "${this.testDetails?.name}"?`,
      title: 'Delete test',
      showClose: false,
      actions: {
        false: 'Cancel',
        true: 'Delete'
      }
    })) {
      let testSuite = (await api.deleteTest(this.testId)).data;
      await this.$router.push({
        name: 'suite-details', params: {
          suiteId: testSuite.id.toString(),
          projectId: testSuite.projectId.toString()
        }
      });
    }
  }

  async copyCodeFromSnippet(code: string) {
    if (!this.testDetails!.code || this.testDetails!.code !== code && await this.$dialog.confirm({
      text: `Your current code will be discarded, would you like to continue?`,
      title: 'Change code',
      showClose: false,
      actions: {
        false: 'No',
        true: 'Yes'
      }
    })) {
      this.testDetails!.code = code;
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

  codeSnippets: any[] = [];

  private async init() {
    this.testDetails = (await api.getTestDetails(this.testId)).data;
    if (this.testDetails) {
      if (this.testDetails.type == null) {
        this.testDetails.type = 'CODE';
      }
      if (this.testDetails.language == null) {
        this.testDetails.language = 'PYTHON';
      }
      if (this.testDetails.code == null) {
        this.testDetails!.code = '';
      }
    }

    this.testDetailsOriginal = _.cloneDeep(this.testDetails);
    this.codeSnippets = [{
      id: 'test_metamorphic_invariance',
      name: 'Metamorphic Invariance',
      type: 'CODE',
      // language=Python
      code: 'perturbation = {\n    "<FEATURE NAME>": lambda x: x["<FEATURE NAME>"] * 2,\n}\n\ntests.metamorphic.test_metamorphic_invariance(\n    df=train_df,\n    model=model,\n    perturbation_dict=perturbation,\n    threshold=0.1\n)'
    }, {
      id: 'test_metamorphic_increasing',
      name: 'Metamorphic Increasing',
      hint: 'Tests that the prediction probability increases with the increase of a feature value',
      type: 'CODE',
      // language=Python
      code: 'tests.metamorphic.test_metamorphic_increasing(\n    df=train_df,\n    model=model,\n    column_name=\'<NUMERIC FEATURE NAME>\',\n    perturbation_percent=0.1,\n    threshold=0.1\n)'
    }, {
      id: 'test_metamorphic_decreasing',
      name: 'Metamorphic Decreasing',
      type: 'CODE',
      hint: 'Tests that the prediction probability decreases with the increase of a feature value',
      // language=Python
      code: 'tests.metamorphic.test_metamorphic_decreasing(\n    df=train_df,\n    model=model,\n    column_name=\'<NUMERIC FEATURE NAME>\',\n    perturbation_percent=0.1,\n    threshold=0.1\n)'
    }, {
      id: 'test_auc',
      name: 'AUC',
      type: 'CODE',
      // language=Python
      code: 'tests.performance.test_auc(\n    test_df,\n    model,\n    threshold=0.1,\n    target=\'<TARGET COLUMN>\'\n)'
    },
      {
        id: 'test_f1',
        name: 'F1',
        type: 'CODE',
        // language=Python
        code: 'tests.performance.test_f1(\n    test_df,\n    model,\n    threshold=0.1,\n    target=\'<TARGET COLUMN>\'\n)'
      },
      {
        id: 'test_diff_f1',
        name: 'F1 difference',
        type: 'CODE',
        // language=Python
        code: 'tests.performance.test_diff_f1(\n    test_df,\n    model,\n    filter_1=test_df[:len(test_df)//2].index,\n    filter_2=test_df[len(test_df)//2:].index,\n    threshold=0.1,\n    target=\'<TARGET COLUMN>\'\n)'
      },
      {
        id: 'test_accuracy',
        name: 'Accuracy',
        type: 'CODE',
        // language=Python
        code: 'tests.performance.test_accuracy(\n    test_df,\n    model,\n    threshold=0.1,\n    target=\'<TARGET COLUMN>\'\n)'
      },
      {
        id: 'test_diff_accuracy',
        name: 'Accuracy difference',
        type: 'CODE',
        // language=Python
        code: 'tests.performance.test_diff_accuracy(\n    test_df,\n    model,\n    filter_1=test_df[:len(test_df)//2].index,\n    filter_2=test_df[len(test_df)//2:].index,\n    threshold=0.1,\n    target=\'<TARGET COLUMN>\'\n)'
      },
      {
        id: 'test_precision',
        name: 'Precision',
        type: 'CODE',
        // language=Python
        code: 'tests.performance.test_precision(\n    test_df,\n    model,\n    threshold=0.1,\n    target=\'<TARGET COLUMN>\'\n)'
      },
      {
        id: 'test_diff_precision',
        name: 'Precision difference',
        type: 'CODE',
        // language=Python
        code: 'tests.performance.test_diff_precision(\n    test_df,\n    model,\n    filter_1=test_df[:len(test_df)//2].index,\n    filter_2=test_df[len(test_df)//2:].index,\n    threshold=0.1,\n    target=\'<TARGET COLUMN>\'\n)'
      },
      {
        id: 'test_recall',
        name: 'Recall',
        type: 'CODE',
        // language=Python
        code: 'tests.performance.test_recall(\n    test_df,\n    model,\n    threshold=0.1,\n    target=\'<TARGET COLUMN>\'\n)'
      },
      {
        id: 'test_diff_recall',
        name: 'Recall difference',
        type: 'CODE',
        // language=Python
        code: 'tests.performance.test_diff_recall(\n    test_df,\n    model,\n    filter_1=test_df[:len(test_df)//2].index,\n    filter_2=test_df[len(test_df)//2:].index,\n    threshold=0.1,\n    target=\'<TARGET COLUMN>\'\n)'
      },
      {
        id: 'test_neg_rmse',
        name: 'Negative RMSE',
        type: 'CODE',
        // language=Python
        code: 'tests.performance.test_neg_rmse(\n    test_df,\n    model,\n    threshold=0.1,\n    target=\'<TARGET COLUMN>\'\n)'
      },
      {
        id: 'test_neg_mae',
        name: 'Negative MAE',
        type: 'CODE',
        // language=Python
        code: 'tests.performance.test_neg_mae(\n    test_df,\n    model,\n    threshold=0.1,\n    target=\'<TARGET COLUMN>\'\n)'
      },
      {
        id: 'test_r2',
        name: 'R2',
        type: 'CODE',
        // language=Python
        code: 'tests.performance.test_r2(\n    test_df,\n    model,\n    threshold=0.1,\n    target=\'<TARGET COLUMN>\'\n)'
      }
    ];
  }
}
</script>

<style scoped lang='scss'>
@import "src/styles/colors.scss";

.mirror {
  transform: rotate(180deg);

}

.editor {
  height: 400px;
  border: 1px solid grey;
}

.snippet {
  cursor: pointer;

  &:hover {
    background-color: $hover;
  }
}
</style>