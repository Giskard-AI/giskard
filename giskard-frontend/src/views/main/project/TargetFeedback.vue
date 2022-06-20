<template>
  <!-- For target feedback -->
  <div>
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
    <v-card v-if='feedbackPopupToggle' class='feedback-card' dark color='primary'>
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
        <v-btn small text light @click='clearFeedback' :disabled='feedbackSubmitted'>cdcdCancel</v-btn>
        <v-btn small class='mx-1' color='white' light @click='submitTargetFeedback'
               :disabled='!(feedback && feedbackChoice) || feedbackSubmitted'>Send
        </v-btn>
        <v-icon color='white' v-show='feedbackSubmitted'>mdi-check</v-icon>
      </v-card-actions>
    </v-card>
  </div>
  <!-- End For general feedback -->
</template>

<script lang='ts'>
import { Component, Prop, Vue } from 'vue-property-decorator';
import OverlayLoader from '@/components/OverlayLoader.vue';
import PredictionResults from './PredictionResults.vue';
import PredictionExplanations from './PredictionExplanations.vue';
import TextExplanation from './TextExplanation.vue';
import { api } from '@/api';
import FeedbackPopover from '@/components/FeedbackPopover.vue';
import Inspector from './Inspector.vue';
import RowList from '@/views/main/project/RowList.vue';
import { CreateFeedbackDTO, DatasetDTO, ModelDTO } from '@/generated-sources';

type CreatedFeedbackTargetDTO = {
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
export default class TargetFeedback extends Vue {
  @Prop() model!: ModelDTO;
  @Prop() dataset!: DatasetDTO;
  @Prop() inputData;
  @Prop() originalData;

  feedbackPopupToggle = false;
  feedback: string = '';
  feedbackChoice = null;
  feedbackError: string = '';
  feedbackSubmitted: boolean = false;

  async mounted(){
    console.log(this.inputData)
  }


  public clearFeedback() {
    this.feedback = '';
    this.feedbackError = '';
    this.feedbackSubmitted = false;
    this.feedbackChoice = null;
    this.feedbackPopupToggle = false;
  }

  get targetFeedbackData(): CreatedFeedbackTargetDTO {
    return {
      projectId: parseInt(this.$router.currentRoute.params.id),
      modelId: this.model.id,
      datasetId: this.dataset.id,
      targetFeature: this.dataset.target,
      userData: JSON.stringify(this.inputData),
      originalData: JSON.stringify(this.originalData)
    };
  }

  public async submitTargetFeedback() {
    console.log("ok")
    const feedback: CreateFeedbackDTO = {
      ...this.targetFeedbackData,
      feedbackType: 'labelling',
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


  private async doSubmitFeedback(payload: CreateFeedbackDTO) {
    await api.submitFeedback(payload, payload.projectId);
  }

}
</script>

<style scoped>


.feedback-card .v-card__title {
  font-size: 1.1rem;
  padding: 8px 12px 0;
}
</style>
