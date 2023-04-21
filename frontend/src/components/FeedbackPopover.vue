<template>
  <v-menu offset-x :close-on-content-click="false" v-model="opened">

    <template v-slot:activator="{ on: onMenu }">
      <v-tooltip right>
        <template v-slot:activator="{ on: onTooltip }">
          <v-btn small icon
                 :color="submittedOnce? 'grey' : 'primary'"
                 v-on="{ ...onMenu, ...onTooltip }">
            <v-icon size=18>mdi-message-plus</v-icon>
          </v-btn>
        </template>
        <span>Feedback</span>
      </v-tooltip>
    </template>

    <v-card dark color="primary">
      <v-card-title>
        <div v-if="originalValue == inputValue">Does the impact of
          <v-chip>{{ inputLabel }}</v-chip>
          on the prediction make sense?
        </div>
        <div v-else>Does the impact of changing
          <v-chip>{{ inputLabel }}</v-chip>
          <span v-show="inputType != 'text'"> from <v-chip color="blue darken-2">{{ originalValue }}</v-chip> to <v-chip
              color="accent">{{ inputValue }}</v-chip></span>
          on the prediction make sense?
        </div>
      </v-card-title>
      <v-card-text>
        <v-radio-group v-model="selected" dark row hide-details>
          <v-radio label="Yes" value="yes"></v-radio>
          <v-radio label="No" value="no"></v-radio>
          <v-radio label="Other" value="other"></v-radio>
        </v-radio-group>
        <v-text-field dense dark outlined single-line hide-details
                      v-model="message"
                      placeholder="Why?"
                      class="message"
        ></v-text-field>
      </v-card-text>
      <v-card-actions>
        <v-btn small text light @click="resetAndClose" :disabled="submitted">Cancel</v-btn>
        <v-btn small color="white" light @click="submitFeedback" :disabled="!(selected && message)">Send</v-btn>
        <span v-show="submitted"><v-icon>mdi-check</v-icon></span>
      </v-card-actions>
    </v-card>
  </v-menu>
</template>

<script lang="ts">
import {Component, Prop, Vue, Watch} from 'vue-property-decorator';

@Component
export default class FeedbackPopover extends Vue {
  @Prop() inputLabel!: any
  @Prop() inputValue!: any
  @Prop() originalValue!: any
  @Prop() inputType!: any

  opened = false
  selected: string | null = null
  message: string = ""
  submitted = false
  submittedOnce = false

  @Watch('selected')
  @Watch('message')
  public resetSubmitted() {
    this.submitted = false;
  }

  public resetAndClose() {
    this.selected = null
    this.message = ""
    this.opened = false
  }

  @Watch('inputValue')
  public resetAll() {
    this.submittedOnce = false
    this.resetAndClose()
  }

  public submitFeedback() {
    const feedback = {
      feedbackChoice: this.selected,
      feedbackMessage: this.message,
      featureName: this.inputLabel,
      featureValue: (this.inputValue !== this.originalValue) ? this.originalValue + " -> " + this.inputValue : this.inputValue,
    }
    this.$emit('submit', feedback)
    this.submitted = true;
    this.submittedOnce = true;
    this.opened = false;
  }
}
</script>

<style scoped lang="scss">
div.v-card {

  opacity: 0.98;
  max-width: 500px;

  & > *:nth-child(-n + 2) { // for the first two children: the title and the content
    padding-bottom: 0px;
  }

  .v-card__title {
    font-size: 1rem;
    padding-top: 8px;
    word-break: normal;
    line-height: 22px;
  }

  .v-input {
    margin-top: 4px;
    margin-bottom: 6px;
  }

  .v-card__actions {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    font-size: 13px;
    color: white;

    * {
      margin: 0 3px
    }
  }
}

.v-chip {
  padding: 8px
}
</style>
