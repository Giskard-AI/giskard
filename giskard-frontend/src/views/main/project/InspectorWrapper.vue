<template>
  <v-container v-if="inspection" fluid>
    <v-row
        align="center"
        no-gutters
        style='height: 60px;'
    >
      <v-toolbar id='data-explorer-toolbar' flat>
        <span class='subtitle-2 mr-2'>Dataset Explorer</span>
        <v-btn icon @click='shuffleMode = !shuffleMode'>
          <v-icon v-if='shuffleMode' color='primary'>mdi-shuffle-variant</v-icon>
          <v-icon v-else>mdi-shuffle-variant</v-icon>
        </v-btn>
        <v-btn :disabled='!canPrevious()' icon @click='previous'>
          <v-icon>mdi-skip-previous</v-icon>
        </v-btn>
        <v-btn :disabled='!canNext()' icon @click='next'>
          <v-icon>mdi-skip-next</v-icon>
        </v-btn>
        <span class='caption grey--text'>Entry #{{ totalRows === 0 ? 0 : rowNb + 1 }} / {{ totalRows }}</span>
        <span v-show="originalData && isDefined(originalData.Index)" class='caption grey--text'
              style='margin-left: 15px'>Row Index {{ originalData.Index + 1 }}</span>
      </v-toolbar>
      <v-spacer/>
      <InspectionFilter
          :is-target-available="isDefined(inspection.dataset.target)"
          :labels="labels"
          :model-type="inspection.model.modelType"
          @input="f=>filter = f"
      />
    </v-row>
    <Inspector :dataset='inspection.dataset'
               :inputData.sync='inputData'
               :model='inspection.model'
               :originalData='originalData'
               class='px-0'
               @reset='resetInput'
               @submitValueFeedback='submitValueFeedback'
               @submitValueVariationFeedback='submitValueVariationFeedback'
    />

    <!-- For general feedback -->
    <v-tooltip left>
      <template v-slot:activator='{ on, attrs }'>
        <v-btn :class="feedbackPopupToggle? 'secondary': 'primary'" bottom fab fixed
               class="zindex-10"
               right
               v-bind='attrs'
               @click='feedbackPopupToggle = !feedbackPopupToggle' v-on='on'
        >
          <v-icon v-if='feedbackPopupToggle'>mdi-close</v-icon>
          <v-icon v-else>mdi-message-plus</v-icon>
        </v-btn>
      </template>
      <span v-if='feedbackPopupToggle'>Close</span>
      <span v-else>Feedback</span>
    </v-tooltip>
    <v-overlay
        :value='feedbackPopupToggle'
        :z-index='10'
    ></v-overlay>
    <v-card v-if='feedbackPopupToggle' id='feedback-card' color='primary' dark>
      <v-card-title>Is this input case insightful?</v-card-title>
      <v-card-text class='px-3 py-0'>
        <v-radio-group v-model='feedbackChoice' class='mb-2 mt-0' dark hide-details row>
          <v-radio label='Yes' value='yes'></v-radio>
          <v-radio label='No' value='no'></v-radio>
          <v-radio label='Other' value='other'></v-radio>
        </v-radio-group>
        <v-textarea
            v-model='feedback'
            :disabled='feedbackSubmitted'
            hide-details
            no-resize
            outlined
            placeholder='Why?'
            rows='2'
        ></v-textarea>
      </v-card-text>
      <p v-if='feedbackError' class='caption error--text mb-0'>{{ feedbackError }}</p>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn :disabled='feedbackSubmitted' light small text @click='clearFeedback'>Cancel</v-btn>
        <v-btn :disabled='!(feedback && feedbackChoice) || feedbackSubmitted' class='mx-1' color='white'
               light small @click='submitGeneralFeedback'>
          Send
        </v-btn>
        <v-icon v-show='feedbackSubmitted' color='white'>mdi-check</v-icon>
      </v-card-actions>
    </v-card>
    <!-- End For general feedback -->
  </v-container>
</template>

<script lang='ts'>
import {Component, Prop, Vue, Watch} from 'vue-property-decorator';
import OverlayLoader from '@/components/OverlayLoader.vue';
import PredictionResults from './PredictionResults.vue';
import PredictionExplanations from './PredictionExplanations.vue';
import TextExplanation from './TextExplanation.vue';
import {api} from '@/api';
import FeedbackPopover from '@/components/FeedbackPopover.vue';
import Inspector from './Inspector.vue';
import Mousetrap from 'mousetrap';
import {CreateFeedbackDTO, Filter, InspectionDTO, ModelType, RowFilterType} from '@/generated-sources';
import mixpanel from "mixpanel-browser";
import _ from "lodash";
import InspectionFilter from './InspectionFilter.vue';

type CreatedFeedbackCommonDTO = {
  targetFeature?: string | null;
  userData: string;
  modelId: number;
  datasetId: number;
  originalData: string;
  projectId: number
};
@Component({
  components: {
    OverlayLoader,
    Inspector,
    PredictionResults,
    FeedbackPopover,
    PredictionExplanations,
    TextExplanation,
    InspectionFilter
  }
})
export default class InspectorWrapper extends Vue {
  @Prop() inspectionId!: number;
  inspection: InspectionDTO | null = null;
  mouseTrap = new Mousetrap();
  loadingData = false;
  inputData = {};
  originalData = {};
  rowNb: number = 0;
  shuffleMode: boolean = false;
  dataErrorMsg = '';

  feedbackPopupToggle = false;
  feedback: string = '';
  feedbackChoice = null;
  feedbackError: string = '';
  feedbackSubmitted: boolean = false;
  labels: string[] = [];
  filter: Filter = {type: RowFilterType.ALL};

  totalRows = 0;
  mt = ModelType;
  rows: Record<string, any>[] = [];
  numberOfRows: number = 0;
  itemsPerPage = 200;
  rowIdxInPage: number = 0;
  regressionThreshold: number = 0.1;
  percentRegressionUnit = true;
  RowFilterType = RowFilterType;

  get commonFeedbackData(): CreatedFeedbackCommonDTO {
    return {
      projectId: parseInt(this.$router.currentRoute.params.id),
      modelId: this.inspection!.model.id,
      datasetId: this.inspection!.dataset.id,
      targetFeature: this.inspection!.dataset.target,
      userData: JSON.stringify(this.inputData),
      originalData: JSON.stringify(this.originalData)
    };
  }

  isDefined(val: any) {
    return !_.isNil(val);
  }

  async init() {
    this.inspection = await api.getInspection(this.inspectionId);
  }

  async mounted() {
    this.labels = await api.getLabelsForTarget(this.inspectionId);
    await this.init();
  }

  bindKeys() {
    this.mouseTrap.bind('left', this.previous);
    this.mouseTrap.bind('right', this.next);
  }

  resetKeys() {
    this.mouseTrap.reset();
  }

  public canPrevious() {
    return !this.shuffleMode && this.rowNb > 0;
  }

  public canNext() {
    return this.rowNb < this.totalRows - 1;
  }

  /**
   * Call on active tab
   */
  async activated() {
    this.bindKeys();
    await this.init();
  }

  deactivated() {
    this.resetKeys();
  }

  public next() {
    if (this.canNext()) {
      this.clearFeedback();
      this.rowNb += 1;
      this.debouncedUpdateRow();
    }
  }

  public previous() {
    if (this.canPrevious()) {
      this.clearFeedback();
      this.rowNb -= 1;
      this.debouncedUpdateRow();
    }
  }

  public clearFeedback() {
    this.feedback = '';
    this.feedbackError = '';
    this.feedbackSubmitted = false;
    this.feedbackChoice = null;
    this.feedbackPopupToggle = false;
  }

  public async submitGeneralFeedback() {
    const feedback: CreateFeedbackDTO = {
      ...this.commonFeedbackData,
      feedbackType: 'general',
      feedbackChoice: this.feedbackChoice,
      feedbackMessage: this.feedback
    };
    try {
      this.feedbackSubmitted = true;
      await this.doSubmitFeedback(feedback);
      this.feedbackPopupToggle = false;
    } catch (err) {
      this.feedbackError = err.response.data.detail;
    }
  }

  public async submitValueFeedback(userData: object) {
    const feedback: CreateFeedbackDTO = {
      ...this.commonFeedbackData,
      feedbackType: 'value',
      ...userData
    };
    await this.doSubmitFeedback(feedback);
  }

  public async submitValueVariationFeedback(userData: object) {
    const feedback: CreateFeedbackDTO = {
      ...this.commonFeedbackData,
      feedbackType: 'value perturbation',
      ...userData
    };
    await this.doSubmitFeedback(feedback);
  }

  private debouncedUpdateRow = _.debounce(async () => {
    await this.updateRow(false);
  }, 150);


  @Watch('inspection.id')
  @Watch('regressionThreshold')
  @Watch('filter', {deep: true, immediate: false})
  @Watch('shuffleMode')
  @Watch('percentRegressionUnit')
  async applyFilter(nv, ov) {
    if (JSON.stringify(nv) === JSON.stringify(ov)) {
      return;
    }
    await this.updateRow(true);
  }

  async updateRow(forceFetch) {
    await this.fetchRows(this.rowNb, forceFetch);
    this.assignCurrentRow(forceFetch)
  }

  /**
   * Calling fetch rows if necessary, i.e. when start or end of the page
   * @param rowIdxInResults index of the row in the results
   * @param forceFetch
   */
  public async fetchRows(rowIdxInResults: number, forceFetch: boolean) {
    const remainder = rowIdxInResults % this.itemsPerPage;
    const newPage = Math.floor(rowIdxInResults / this.itemsPerPage);
    if ((rowIdxInResults > 0 && remainder === 0) || forceFetch) {
      await this.fetchRowsByRange(newPage * this.itemsPerPage, (newPage + 1) * this.itemsPerPage);
    }
  }

  /**
   * Requesting the filtered rows in a given range
   * @param minRange
   * @param maxRange
   */
  public async fetchRowsByRange(minRange: number, maxRange: number) {
    const props = {
      'modelId': this.inspection?.model.id,
      'minRange': minRange,
      'maxRange': maxRange,
      'isRandom': this.shuffleMode
    };
    const response = await api.getDataFilteredByRange(this.inspection?.id, props, this.filter);
    this.rows = response.data;
    this.numberOfRows = response.rowNb;
  }

  private assignCurrentRow(forceFetch: boolean) {
    this.rowIdxInPage = this.rowNb % this.itemsPerPage;
    this.loadingData = true;

    this.inputData = this.rows[this.rowIdxInPage];
    this.originalData = {...this.inputData}; // deep copy to avoid caching mechanisms
    this.dataErrorMsg = '';
    this.loadingData = false;
    this.totalRows = this.numberOfRows;
    if (forceFetch) {
      this.rowNb = 0;
    }
  }

  private resetInput() {
    this.inputData = {...this.originalData};
  }

  private async doSubmitFeedback(payload: CreateFeedbackDTO) {
    mixpanel.track('Submit feedback', {
      datasetId: payload.datasetId,
      feedbackChoice: payload.feedbackChoice,
      feedbackType: payload.feedbackType,
      modelId: payload.modelId,
      projectId: payload.projectId
    });
    await api.submitFeedback(payload, payload.projectId);
  }


}
</script>

<style scoped>
#data-explorer-toolbar .v-btn {
  height: 36px;
  width: 36px;
}

#feedback-card {
  z-index: 10;
  width: 42vw;
  position: fixed;
  opacity: 0.96;
  right: 8px;
  bottom: 80px;
}
.zindex-10{
  z-index: 10;
}
#feedback-card .v-card__title {
  font-size: 1.1rem;
  padding: 8px 12px 0;
}
</style>
