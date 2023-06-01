<template>
  <div class="vc">
    <v-tabs centered class="vc">
      <v-tab>Tests</v-tab>
      <v-tab>Test suites</v-tab>
      <v-tab-item :transition="false" key="1" class="vc">
        <div class="vc">
          <v-container class="main-container vc">
            <v-row class="fill-height">
              <v-col cols="4" class="vc fill-height">
                <v-list three-line v-if="testFunctions">
                  <v-list-item-group v-model="selected" color="primary" mandatory>
                    <template v-for="(test, index) in testFunctions">
                      <v-divider/>
                      <v-list-item :value="test">
                        <v-list-item-content>
                          <v-list-item-title v-text="test.name" class="test-title"></v-list-item-title>

                          <v-list-item-subtitle v-if="test.tags">
                            <v-chip class="mr-2" v-for="tag in sorted(test.tags)" x-small :color="pasterColor(tag)">
                              {{ tag }}
                            </v-chip>
                          </v-list-item-subtitle>
                        </v-list-item-content>

                      </v-list-item>
                    </template>
                  </v-list-item-group>
                </v-list>
              </v-col>
              <v-col cols="8" v-if="selected" class="vc fill-height">
                <div class="d-flex justify-space-between">
                  <span class="text-h5">{{ selected.name }}</span>
                  <v-btn small outlined tile class="primary" color="white">
                    <v-icon dense class="pr-2">mdi-plus</v-icon>
                    Add to test suite
                  </v-btn>
                </div>
                <div class="vc overflow-x-hidden pr-5">

                  <pre class="test-doc caption pt-5">{{ selected.doc }}</pre>
                  <div class="pt-5">
                    <div class="d-flex justify-space-between">
                      <span class="text-h6">Inputs</span>
                      <v-btn width="100" small tile outlined @click="tryMode = !tryMode">{{
                          tryMode ? 'Cancel' : 'Try it'
                        }}
                      </v-btn>
                    </div>
                    <v-list>
                      <v-list-item v-for="a in selected.arguments" class="pl-0 pr-0">
                        <v-row>
                          <v-col>
                            <v-list-item-content>
                              <v-list-item-title>{{ a.name }}</v-list-item-title>
                              <v-list-item-subtitle class="text-caption">{{ a.type }}</v-list-item-subtitle>
                              <v-list-item-action-text v-show="!!a.optional">Optional. Default: <code>{{
                                  a.default
                                }}</code>
                              </v-list-item-action-text>
                            </v-list-item-content>
                          </v-col>
                          <v-col>
                            <template v-if="tryMode">
                              <DatasetSelector :project-id="projectId" :label="a.name" :return-object="false"
                                               v-if="a.type === 'GiskardDataset'" :value.sync="testArguments[a.name]"/>
                              <ModelSelector :project-id="projectId" :label="a.name" :return-object="false"
                                             v-if="a.type === 'GiskardModel'" :value.sync="testArguments[a.name]"/>
                              <v-text-field
                                  :step='a.type === "float" ? 0.1 : 1'
                                  v-model="testArguments[a.name]"
                                  v-if="['float', 'int'].includes(a.type)"
                                  hide-details
                                  single-line
                                  type="number"
                                  outlined
                                  dense
                              />
                            </template>
                          </v-col>
                        </v-row>
                      </v-list-item>
                    </v-list>
                    <v-row v-show="tryMode">
                      <v-col :align="'right'">
                        <v-btn width="100" small tile outlined class="primary" color="white" @click="runTest">Run
                        </v-btn>
                      </v-col>
                    </v-row>
                    <v-row style="height: 150px">
                      <v-col v-if="testResult">
                        <TestExecutionResultBadge :result="testResult"/>
                      </v-col>
                    </v-row>
                  </div>
                </div>

              </v-col>
            </v-row>
          </v-container>
        </div>
      </v-tab-item>
      <v-tab-item :transition="false" key="2" class="vc">
        <div class="vc">
          <div class="debug">row</div>
        </div>
      </v-tab-item>
    </v-tabs>

  </div>
</template>

<script lang="ts">
import {Component, Prop, Vue, Watch} from "vue-property-decorator";
import {api} from "@/api";
import {FeedbackMinimalDTO} from "@/generated-sources";
import {pasterColor} from "@/utils";
import _ from "lodash";
import DatasetSelector from "@/views/main/utils/DatasetSelector.vue";
import ModelSelector from "@/views/main/utils/ModelSelector.vue";
import TestExecutionResultBadge from "@/views/main/project/TestExecutionResultBadge.vue";

@Component({
  components:
      {
        DatasetSelector, ModelSelector, TestExecutionResultBadge
      }
})
export default class TestsCatalog extends Vue {
  @Prop({required: true}) projectId!: number;
  pasterColor = pasterColor;
  registry: any[] = [];
  selected: any | null = null;
  tryMode = true
  testArguments = {}
  testResult: any = null;

  feedbacks: FeedbackMinimalDTO[] = [];
  search = "";
  modelFilter = "";
  datasetFilter = "";
  typeFilter = "";
  groupByFeature = false

  openFeedbackDetail = false

  private async runTest() {
    this.testResult = await api.runAdHocTest(this.selected.id, this.testArguments);
  }

  get selectedTags() {
    return _.orderBy(this.selected.tags);
  }

  private castDefaultValueToType(arg) {
    switch (arg.type) {
      case 'float':
        return parseFloat(arg.default)
      case 'int':
        return parseInt(arg.default)
      default:
        return arg.default;
    }
  }

  @Watch('selected')
  public setSelected() {
    this.testResult = null;
    this.tryMode = false;
    this.testArguments = {}
    for (const [argName, arg] of Object.entries(this.selected.arguments)) {
      this.testArguments[argName] = this.castDefaultValueToType(arg);
    }
  }

  sorted(arr: any[]) {
    const res = _.cloneDeep(arr);
    res.sort()
    return res;
  }

  get testFunctions() {
    // @ts-ignore
    return _.sortBy(this.registry.functions, 'name');
  }

  async activated() {
    this.registry = await api.getTestsRegistry();
    if (this.testFunctions) {
      this.selected = this.testFunctions[0];
    }

  }

  @Watch("$route", {deep: true})
  setOpenFeedbackDetail(to) {
    this.openFeedbackDetail = to.meta && to.meta.openFeedbackDetail
  }

  get tableHeaders() {
    return [
      {
        text: "Model",
        sortable: true,
        value: "modelName",
        align: "left",
        filter: (value) => !this.modelFilter ? true : value == this.modelFilter,
      },
      {
        text: "Dataset",
        sortable: true,
        value: "datasetName",
        align: "left",
        filter: (value) => !this.datasetFilter ? true : value == this.datasetFilter,
      },
      {
        text: "User ID",
        sortable: true,
        value: "userLogin",
        align: "left",
      },
      {
        text: 'On',
        value: 'createdOn',
        sortable: true,
        filterable: false,
        align: 'left'
      },
      {
        text: "Type",
        sortable: true,
        value: "feedbackType",
        align: "left",
        filter: (value) => !this.typeFilter ? true : value == this.typeFilter,
      },
      {
        text: "Feature name",
        sortable: true,
        value: "featureName",
        align: "left",
      },
      {
        text: "Feature value",
        sortable: true,
        value: "featureValue",
        align: "left",
      },
      {
        text: "Choice",
        sortable: true,
        value: "feedbackChoice",
        align: "left",
      },
      {
        text: "Message",
        sortable: true,
        value: "feedbackMessage",
        align: "left",
      },
    ];
  }

  get existingModels() {
    return this.feedbacks.map((e) => e.modelName);
  }

  get existingDatasets() {
    return this.feedbacks.map((e) => e.datasetName);
  }

  get existingTypes() {
    return this.feedbacks.map((e) => e.feedbackType);
  }

  public async fetchFeedbacks() {
    this.feedbacks = await api.getProjectFeedbacks(this.projectId);
  }

  public async openFeedback(obj) {
    await this.$router.push({name: 'feedback-detail', params: {feedbackId: obj.id}})
  }

}
</script>

<style scoped lang="scss">
.main-container {
  width: 100%;
  max-width: 100%;
}

.test-title {
  white-space: break-spaces;
}

.box-grow {
  flex: 1; /* formerly flex: 1 0 auto; */
  background: green;
  padding: 5px;
  margin: 5px;
  min-height: 0; /* new */
}

.test-doc {
  white-space: break-spaces;
}


</style>
