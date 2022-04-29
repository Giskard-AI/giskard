<template>
  <v-container fluid>
    <v-toolbar flat height="32" id="data-explorer-toolbar">
      <span class="subtitle-2 mr-2">Dataset Explorer</span>
      <v-btn icon @click="shuffleMode = !shuffleMode">
        <v-icon v-if="shuffleMode" color="primary">mdi-shuffle-variant</v-icon>
        <v-icon v-else>mdi-shuffle-variant</v-icon>
      </v-btn>
      <v-btn icon @click="previous" :disabled="shuffleMode || rowNb == 0"><v-icon>mdi-skip-previous</v-icon></v-btn>
      <v-btn icon @click="next"><v-icon>mdi-skip-next</v-icon></v-btn>
      <span class="caption grey--text">Entry #{{rowNb}}</span>
    </v-toolbar>

    <Inspector class="px-0"
      :modelId="modelId"
      :datasetId="datasetId"
      :originalData="originalData"
      :inputData.sync="inputData"
      :targetFeature="targetFeature"
      @reset="resetInput"
      @submitValueFeedback="submitValueFeedback"
      @submitVariationFeedback="submitValueVariationFeedback"
    />

    <!-- For general feedback -->
    <v-tooltip left>
      <template v-slot:activator="{ on, attrs }">
      <v-btn fab fixed bottom right
        @click="feedbackPopupToggle = !feedbackPopupToggle"
        :class="feedbackPopupToggle? 'secondary': 'primary'"
        v-bind="attrs" v-on="on"
        >
        <v-icon v-if="feedbackPopupToggle">mdi-close</v-icon>
        <v-icon v-else>mdi-message-plus</v-icon>
      </v-btn>
      </template>
      <span v-if="feedbackPopupToggle">Close</span>
      <span v-else>Feedback</span>
    </v-tooltip>
    <v-overlay
      :value="feedbackPopupToggle"
      :z-index="1"
    ></v-overlay>
    <v-card v-if="feedbackPopupToggle" id="feedback-card" dark color="primary">
      <v-card-title>Is this input case insightful?</v-card-title>
      <v-card-text class="px-3 py-0">
        <v-radio-group v-model="feedbackChoice" dark row hide-details class="mb-2 mt-0">
          <v-radio label="Yes" value="yes"></v-radio>
          <v-radio label="No" value="no"></v-radio>
          <v-radio label="Other" value="other"></v-radio>
        </v-radio-group>
        <v-textarea
          v-model="feedback"
          :disabled="feedbackSubmitted"
          placeholder="Why?"
          rows=2
          no-resize
          outlined
          hide-details
        ></v-textarea>
      </v-card-text>
      <p v-if="feedbackError" class="caption error--text mb-0">{{ feedbackError }}</p>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn small text light @click="clearFeedback" :disabled="feedbackSubmitted">Cancel</v-btn>
        <v-btn small class="mx-1" color="white" light @click="submitGeneralFeedback"
          :disabled="!(feedback && feedbackChoice) || feedbackSubmitted">Send</v-btn>
        <v-icon color="white" v-show="feedbackSubmitted">mdi-check</v-icon>
      </v-card-actions>
    </v-card>
    <!-- End For general feedback -->
  </v-container>
</template>

<script lang="ts">
import { Component, Vue, Prop, Watch } from 'vue-property-decorator';
import OverlayLoader from '@/components/OverlayLoader.vue';
import PredictionResults from './PredictionResults.vue';
import PredictionExplanations from './PredictionExplanations.vue';
import TextExplanation from './TextExplanation.vue';
import { api } from '@/api';
import { readToken } from '@/store/main/getters';
import { IFeedbackCreate } from '@/interfaces';
import FeedbackPopover from '@/components/FeedbackPopover.vue';
import Inspector from './Inspector.vue';
import Mousetrap from 'mousetrap';

@Component({
  components: { OverlayLoader, Inspector, PredictionResults, FeedbackPopover, PredictionExplanations, TextExplanation }
})
export default class InspectorWrapper extends Vue {
	@Prop({ required: true }) modelId!: number
	@Prop({ required: true }) datasetId!: number
  @Prop() targetFeature!: string

  mouseTrap= new Mousetrap();
  loadingData = false;
  inputData = {}
  originalData = {}
  rowNb: number = 0
  shuffleMode: boolean = false
  dataErrorMsg = ""

  feedbackPopupToggle = false
  feedback = ""
  feedbackChoice = null
  feedbackError = ""
  feedbackSubmitted = false

  async mounted() {
    await this.fetchRowData(0);
  }

  bindKeys() {
    this.mouseTrap.bind('left', this.previous);
    this.mouseTrap.bind('right', this.next);
  }

  resetKeys() {
    this.mouseTrap.reset();
  }

  /**
   * Call on active tab
   */
  activated() {
    this.bindKeys();
  }

  deactivated() {
    this.resetKeys();
  }

  public next() {
    this.clearFeedback();
    this.fetchRowData(this.rowNb + 1);
  }
  public previous() {
    this.clearFeedback();
    this.fetchRowData(Math.max(0, this.rowNb - 1))
  }

  @Watch("datasetId")
  async reload() {
    await this.fetchRowData(0)
  }

  private async fetchRowData(rowId) {
    try {
      this.loadingData = true
      const resp = this.shuffleMode
        ? await api.getDataRandom(readToken(this.$store), this.datasetId)
        : await api.getDataByRowId(readToken(this.$store), this.datasetId, rowId)
      this.inputData = resp.data
      this.originalData = {...this.inputData} // deep copy to avoid caching mechanisms
      this.rowNb = resp.data.rowNb
      this.dataErrorMsg = "";
    } catch (error) {
      this.dataErrorMsg = error.response.data.detail
    } finally {
      this.loadingData = false
    }
  }

  private resetInput() {
    this.inputData = {...this.originalData}
  }

  public clearFeedback() {
    this.feedback = ""
    this.feedbackError = ""
    this.feedbackSubmitted = false
    this.feedbackChoice = null
    this.feedbackPopupToggle = false;
  }

  get commonFeedbackData() {
    return {
      project_id: parseInt(this.$router.currentRoute.params.id),
      model_id: this.modelId,
      dataset_id: this.datasetId,
      target_feature: this.targetFeature,
      user_data: this.inputData,
      original_data: this.originalData
    }
  }

  public async submitGeneralFeedback() {
    const feedback: IFeedbackCreate = {
      ...this.commonFeedbackData,
      feedback_type: "general",
      feedback_choice: this.feedbackChoice || undefined,
      feedback_message: this.feedback
    }
    try {
      await this.doSubmitFeedback(feedback)
      this.feedbackSubmitted = true
    } catch (err) {
      this.feedbackError = err.response.data.detail
    }
  }

  public async submitValueFeedback(userData: object) {
    const feedback: IFeedbackCreate = {
      ...this.commonFeedbackData,
      feedback_type: "value",
      ...userData
    }
    await this.doSubmitFeedback(feedback)
  }

  public async submitValueVariationFeedback(userData: object) {
    const feedback: IFeedbackCreate = {
      ...this.commonFeedbackData,
      feedback_type: "value perturbation",
      ...userData
    }
    await this.doSubmitFeedback(feedback)
  }

  private async doSubmitFeedback(payload: IFeedbackCreate) {
    await api.submitFeedback(readToken(this.$store), payload, payload.project_id)
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
    padding: 0 12px;
    padding-top: 8px;
}
</style>
