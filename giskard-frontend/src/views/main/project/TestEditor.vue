<template>
  <ValidationObserver v-slot='{ invalid }' v-if='testDetails' class="vertical-container">

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
    <v-row class="flex-grow-1">
      <v-col :cols='3' v-show="!fullScreen">
        <v-alert
            text
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
              <td><code>actual_ds</code></td>
              <td>Actual dataset</td>
            </tr>
            <tr>
              <td><code>reference_ds</code></td>
              <td>Reference dataset</td>
            </tr>
          </table>
          <div class='mt-4 mb-0'>
            <p class='ma-0'>These variables will be provided at the test execution time</p>
            <p class='ma-0'>you can reference them in the custom test script</p>
          </div>
        </v-alert>

      </v-col>
      <v-col :cols='fullScreen ? 12 : 6' class="vertical-container">
        <div class="editor-wrapper" :class="{'tall' : fullScreen}">
          <MonacoEditor
              ref="editor"
              v-if="testDetails.type === 'CODE'"
              v-model='testDetails.code'
              class='editor'
              :class="{'tall' : fullScreen}"
              language='python'
              :options='$root.monacoOptions'
          />
          <v-tooltip left>
            <template v-slot:activator="{ on, attrs }">
              <v-btn
                  class="code-editor-resize"
                  v-bind="attrs"
                  v-on="on"
                  icon
                  @click="fullScreen = !fullScreen;"
                  v-track-click="'Resize test code editor: '+(fullScreen?'min':'max')"
              >
                <v-icon>{{ fullScreen ? 'mdi-fullscreen-exit' : 'mdi-fullscreen' }}</v-icon>
              </v-btn>
            </template>
            <span>{{ fullScreen ? 'Minimize' : 'Maximize' }}</span>
          </v-tooltip>
        </div>
      </v-col>
      <v-col :cols='3' v-if="!fullScreen" class="vertical-container">
        <v-list class="templates-list">
          <v-subheader>Code presets</v-subheader>
          <div style="max-height: 0;">
            <v-list-group
                v-for='snippet in codeSnippets'
                :key='snippet.title'
                v-model='snippet.active'
                no-action
            >
              <template v-slot:activator>
                <v-list-item-content>
                  <v-list-item-title v-text='snippet.title'></v-list-item-title>
                </v-list-item-content>
              </template>
              <template v-for='child in snippet.items'>
                <v-hover v-slot='{ hover }' class='snippet pl-3'>
                  <v-list-item :key='child.title' @click='copyCodeFromSnippet(child.code)'
                               :disabled="!testAvailability[child['id']]">
                    <v-list-item-icon>
                      <v-icon class='mirror code-snippet-icon' v-show='hover' dense>exit_to_app</v-icon>
                    </v-list-item-icon>
                    <v-list-item-content>
                      <v-list-item-title v-text='child.title'></v-list-item-title>
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
                        <span>{{ child.hint }}</span>
                      </v-tooltip>
                    </v-list-item-action>
                  </v-list-item>
                </v-hover>
              </template>
            </v-list-group>
          </div>
        </v-list>
      </v-col>
    </v-row>
    <v-row style="height: 120px">
      <v-col align-self="end" cols="3">
        <v-btn tile color='primary'
               class='mr-3'
               :disabled='!isDirty() || invalid'
               @click='save()'>
          <v-icon dense left>save</v-icon>
          Save
        </v-btn>
        <v-btn
            color="primary"
            tile
            @click='runTest()'
            :loading='executingTest'
            :disabled='executingTest'
        >
          <v-icon>arrow_right</v-icon>
          <span>Run</span>
        </v-btn>

      </v-col>
      <v-col v-if='runResult' align-self="end" class="flex-grow-1" cols="6">
        <v-alert
            v-model='showRunResult'
            border='left'
            type='error'
            v-if="runResult.status === 'ERROR'">
          {{ runResult.message }}
        </v-alert>
        <template v-for='testResult in runResult.result'>
          <v-alert
              tile
              class="test-results"
              :color="getBadgeColor(runResult.status)"
              v-model='showRunResult'
              :type="testResult.result.passed ? 'success' : 'error'"
              dismissible
              close-icon="mdi-close"
          >
            <div class="d-flex justify-space-between align-center">
              <div class='text-h6'>Test {{ testResult.result.passed ? 'passed' : 'failed' }}</div>
              <div class="text-body-2">{{ runResult.executionDate | date }}</div>
            </div>
            <div class="d-flex justify-space-between align-center">
              <div class='text-body-2'>Metric: {{ testResult.result.metric }}</div>
              <div class='text-body-2' v-if="testResult.result.messages && testResult.result.messages.length">
                {{ testResult.result.messages[0].text }}
              </div>
              <!--              <a class="text-body-2 results-link text-decoration-underline">Full results</a>-->
            </div>
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
import * as monaco from 'monaco-editor';

import Component from 'vue-class-component';
import {Prop, Watch} from 'vue-property-decorator';
import {api} from '@/api';
import _ from 'lodash';
import numeral from 'numeral';
import {CodeTestCollection, TestDTO, TestExecutionResultDTO, TestResult, TestType} from '@/generated-sources';
import mixpanel from "mixpanel-browser";
import {testStatusToColor} from "@/views/main/tests/test-utils";
import Mousetrap from "mousetrap";


Vue.filter('formatNumber', function (value, fmt) {
  return numeral(value).format(fmt || '0.0'); // displaying other groupings/separators is possible, look at the docs
});

@Component({components: {MonacoEditor}})
export default class TestEditor extends Vue {
  @Prop({required: true}) testId!: number;
  @Prop({required: true}) suiteId!: number;
  testDetails: TestDTO | null = null;
  testDetailsOriginal: TestDTO | null = null;
  showRunResult: boolean = false;
  runResult: TestExecutionResultDTO | null = null;
  executingTest = false;
  testAvailability: { [p: string]: boolean } = {};
  fullScreen = false;
  mouseTrap = new Mousetrap();

  get editor() {
    return this.$refs.editor?.editor;
  }


  async mounted() {
    await this.init();
    this.resizeEditor();
    this.setUpKeyBindings();
  }

  destroyed() {
    this.mouseTrap.reset();
  }

  isDirty() {
    return !_.isEqual(this.testDetailsOriginal, this.testDetails);
  }

  @Watch('fullScreen')
  resizeEditor() {
    setTimeout(() => {
      this.editor.layout();
    });
  }

  async save() {
    if (!this.isDirty()) {
      return;
    }
    if (this.testDetails) {
      mixpanel.track('Save test', {
            testId: this.testDetails.id,
            suiteId: this.testDetails.suiteId,
            language: this.testDetails.language,
            type: this.testDetails.type
          }
      );
      this.testDetailsOriginal = await api.saveTest(this.testDetails);
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
      let testSuite = await api.deleteTest(this.testId);
      mixpanel.track('Delete test', {testId: this.testId, projectId: testSuite.project.id});
      await this.$router.push({
        name: 'suite-details', params: {
          suiteId: testSuite.id.toString(),
          projectId: testSuite.project.id.toString()
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
    mixpanel.track('Run test', {testId: this.testId});

    try {
      this.executingTest = true;

      this.resetTestResults();

      if (this.isDirty()) {
        await this.save();
      }
      this.runResult = await api.runTest(this.testId);
      if (this.runResult?.status === TestResult.ERROR) {
        mixpanel.track('Test error', {testId: this.testId, message: this.runResult.message});
      }
    } finally {
      this.executingTest = false;
    }

  }

  private resetTestResults() {
    this.showRunResult = true;
    this.runResult = null;
  }

  codeSnippets: CodeTestCollection[] = [];

  private async init() {
    this.testDetails = await api.getTestDetails(this.testId);
    if (this.testDetails) {
      if (this.testDetails.type == null) {
        this.testDetails.type = TestType.CODE;
      }
      if (this.testDetails.code == null) {
        this.testDetails.code = '';
      }
    }

    this.testDetailsOriginal = _.cloneDeep(this.testDetails);
    await this.loadTestTemplates();

  }

  private async loadTestTemplates() {
    let response = await api.getCodeTestTemplates(this.suiteId);
    this.testAvailability = response.testAvailability;
    this.codeSnippets = response.collections;
    this.codeSnippets.sort((a, b) => {
      if (!this.testAvailability[a.id]) {
        return a.order - b.order
      }
      return a.order - b.order;
    });
    this.codeSnippets.forEach(collection => {
      collection.items.sort((a, b) => {
        return (this.testAvailability[b.id] ? 1 : 0) - (this.testAvailability[a.id] ? 1 : 0);
      });
    });
  }

  getBadgeColor(testStatus: TestResult) {
    return testStatusToColor(testStatus);
  }

  private setUpKeyBindings() {
    this.mouseTrap.bind(['command+s', 'ctrl+s'], () => {
      this.save();
      return false;
    });

    this.mouseTrap.bind(['command+enter', 'ctrl+enter'], () => {
      this.runTest();
      return false;
    });
    this.mouseTrap.bind(['command+shift+f', 'ctrl+shift+f'], () => {
      this.fullScreen = !this.fullScreen;
      return false;
    });

    this.editor.addAction({
      id: 'editor-save',
      label: 'editor-save',
      keybindings: [
        monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS,
        monaco.KeyMod.WinCtrl | monaco.KeyCode.KeyS,
      ],
      run: this.save
    });

    this.editor.addAction({
      id: 'editor-run',
      label: 'editor-run',
      keybindings: [
        monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter,
        monaco.KeyMod.WinCtrl | monaco.KeyCode.Enter,
      ],
      run: this.runTest
    });
    this.editor.addAction({
      id: 'editor-resize',
      label: 'editor-resize',
      keybindings: [
        monaco.KeyMod.CtrlCmd | monaco.KeyMod.Shift | monaco.KeyCode.KeyF,
        monaco.KeyMod.WinCtrl | monaco.KeyMod.Shift | monaco.KeyCode.KeyF
      ],
      run: () => {
        this.fullScreen = !this.fullScreen;
      }
    });

  }
}
</script>

<style scoped lang='scss'>
@import "src/styles/colors.scss";

.editor-wrapper {
  position: relative;
  min-height: 300px;
  flex-grow: 1;
}

.mirror {
  transform: rotate(180deg);

}

.templates-list {
  overflow: auto;
  flex-grow: 1;
  padding: 0;
}

.code-editor-resize {
  position: absolute;
  top: 5px;
  right: 15px;
  z-index: 100;
}

.editor {
  height: 100%;
  border: 1px solid grey;

  ::v-deep .suggest-widget {
    display: none;
  }

}

.tall {
  flex-grow: 1;
}

.snippet {
  cursor: pointer;

  .code-snippet-icon {
    font-size: 16px;
  }

  &:hover {
    background-color: $hover;
  }
}

::v-deep .test-results {
  .v-icon {
    align-self: center;
  }
}

.results-link {
  color: #ffffff;
}

::v-deep .v-alert {
  margin: 0;
}
</style>