<template>
  <v-container fluid v-if="inspection">
    <v-row
      no-gutters
      style='height: 60px;'
    >
      <v-toolbar flat id='data-explorer-toolbar'>
        <span class='subtitle-2 mr-2'>Dataset Explorer</span>
        <v-btn icon @click='shuffleMode = !shuffleMode'>
          <v-icon v-if='shuffleMode' color='primary'>mdi-shuffle-variant</v-icon>
          <v-icon v-else>mdi-shuffle-variant</v-icon>
        </v-btn>
        <v-btn icon @click='previous' :disabled='!canPrevious()'>
          <v-icon>mdi-skip-previous</v-icon>
        </v-btn>
        <v-btn icon @click='next' :disabled='!canNext()'>
          <v-icon>mdi-skip-next</v-icon>
        </v-btn>
        <span class='caption grey--text'>Entry #{{ totalRows === 0 ? 0 : rowNb+1 }} / {{ totalRows }}</span>
        <span style='margin-left: 15px' class='caption grey--text'>Row Index {{ originalData.Index +1 }}</span>
      </v-toolbar>
    </v-row>

    <RowList ref='rowList'
             v-if="inspection"
             :inspection='inspection'
             :currentRowIdx='rowNb'
             :shuffleMode='shuffleMode'
             @fetchedRow='getCurrentRow'
    />
    <Inspector class='px-0'
               :model='inspection.model'
               :dataset='inspection.dataset'
               :originalData='originalData'
               :inputData.sync='inputData'
               @reset='resetInput'
               @submitValueFeedback='submitValueFeedback'
               @submitVariationFeedback='submitValueVariationFeedback'
    />

    <!-- For general feedback -->
    <v-tooltip left>
      <template v-slot:activator='{ on, attrs }'>
        <v-btn fab fixed bottom right
               @click='feedbackPopupToggle = !feedbackPopupToggle'
               :class="feedbackPopupToggle? 'secondary': 'primary'"
               v-bind='attrs' v-on='on'
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
      :z-index='1'
    ></v-overlay>
    <v-card v-if='feedbackPopupToggle' id='feedback-card' dark color='primary'>
      <v-card-title>Is this input case insightful?</v-card-title>
      <v-card-text class='px-3 py-0'>
        <v-radio-group v-model='feedbackChoice' dark row hide-details class='mb-2 mt-0'>
          <v-radio label='Yes' value='yes'></v-radio>
          <v-radio label='No' value='no'></v-radio>
          <v-radio label='Other' value='other'></v-radio>
        </v-radio-group>
        <v-textarea
          v-model='feedback'
          :disabled='feedbackSubmitted'
          placeholder='Why?'
          rows='2'
          no-resize
          outlined
          hide-details
        ></v-textarea>
      </v-card-text>
      <p v-if='feedbackError' class='caption error--text mb-0'>{{ feedbackError }}</p>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn small text light @click='clearFeedback' :disabled='feedbackSubmitted'>Cancel</v-btn>
        <v-btn small class='mx-1' color='white' light @click='submitGeneralFeedback'
               :disabled='!(feedback && feedbackChoice) || feedbackSubmitted'>Send
        </v-btn>
        <v-icon color='white' v-show='feedbackSubmitted'>mdi-check</v-icon>
      </v-card-actions>
    </v-card>
    <!-- End For general feedback -->
  </v-container>
</template>

<script lang='ts'>
import {Component, Prop, Vue} from 'vue-property-decorator';
import OverlayLoader from '@/components/OverlayLoader.vue';
import PredictionResults from './PredictionResults.vue';
import PredictionExplanations from './PredictionExplanations.vue';
import TextExplanation from './TextExplanation.vue';
import {api} from '@/api';
import {readToken} from '@/store/main/getters';
import FeedbackPopover from '@/components/FeedbackPopover.vue';
import Inspector from './Inspector.vue';
import Mousetrap from 'mousetrap';
import RowList from '@/views/main/project/RowList.vue';
import {CreateFeedbackDTO, InspectionDTO} from '@/generated-sources';

type CreatedFeedbackCommonDTO = {
  targetFeature: string;
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
    RowList
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

  totalRows = 0;

  async init(){
    this.inspection = await api.getInspection(this.inspectionId);
  }

  async mounted() {
    await this.init();
  }

  private getCurrentRow(rowDetails, totalRows: number, hasFilterChanged: boolean) {
    this.loadingData = true;
    this.inputData = rowDetails;
    this.originalData = { ...this.inputData }; // deep copy to avoid caching mechanisms
    this.dataErrorMsg = '';
    this.loadingData = false;
    this.totalRows = totalRows;
    if (hasFilterChanged) {
      this.rowNb = 0;
    }
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

  public async next() {
    this.clearFeedback();
    this.rowNb += 1;
  }

  public async previous() {
    if (this.canPrevious()) {
      this.clearFeedback();
      this.rowNb -= 1;
    }
  }


  private resetInput() {
    this.inputData = { ...this.originalData };
  }

  public clearFeedback() {
    this.feedback = '';
    this.feedbackError = '';
    this.feedbackSubmitted = false;
    this.feedbackChoice = null;
    this.feedbackPopupToggle = false;
  }

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

  public async submitGeneralFeedback() {
    const feedback: CreateFeedbackDTO = {
      ...this.commonFeedbackData,
      feedbackType: 'general',
      feedbackChoice: this.feedbackChoice,
      feedbackMessage: this.feedback
    };
    try {
      await this.doSubmitFeedback(feedback);
      this.feedbackSubmitted = true;
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

  private async doSubmitFeedback(payload: CreateFeedbackDTO) {
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
  z-index: 2;
  width: 42vw;
  position: fixed;
  opacity: 0.96;
  right: 8px;
  bottom: 80px;
}

#feedback-card .v-card__title {
  font-size: 1.1rem;
  padding: 8px 12px 0;
}
</style>
