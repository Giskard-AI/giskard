<template>
  <v-tabs v-if="data">
    <v-tab>Overview</v-tab>
    <v-tab>Inspector</v-tab>
    <v-tab-item class="height85vh">
      <div class="d-flex flex-column metadata fill-height align-baseline">
        <v-container class="w100 flex-grow-1 ">
          <v-row class="grow">
            <v-col md=5>
              <v-card class="scrollable max75vh">
                <v-card-text>
                  <v-row>
                    <v-col>
                      <div class="caption font-weight-light">Originator</div>
                      <div class="subtitle-2">{{ data.user.displayName || data.user.user_id }}</div>
                      <div class="caption font-weight-light">Sent On</div>
                      <div class="subtitle-2">{{ data.createdOn | date }}</div>
                      <div class="caption font-weight-light">Model</div>
                      <div class="subtitle-2">{{ data.model.fileName }}</div>
                      <div class="caption font-weight-light">Dataset File</div>
                      <div class="subtitle-2">{{ data.dataset.fileName }}</div>
                    </v-col>
                    <v-col>
                      <div class="caption font-weight-light">Feedback Type</div>
                      <div class="subtitle-2">{{ data.feedbackType }}</div>
                      <div class="caption font-weight-light">Feedback Choice</div>
                      <div class="subtitle-2">{{ data.feedbackChoice }}</div>
                      <div class="caption font-weight-light">Feature</div>
                      <div class="subtitle-2">{{ data.featureName || "-" }}</div>
                      <div class="caption font-weight-light">Feature Value</div>
                      <div class="subtitle-2">{{ data.featureValue || "-" }}</div>
                    </v-col>
                  </v-row>
                </v-card-text>
              </v-card>
            </v-col>
            <v-col md=7>
              <v-card class="scrollable max75vh">
                <v-card-title>Discussion</v-card-title>
                <v-card-text>
                  <MessageReply
                      :author="data.user"
                      :created-on="data.createdOn"
                      :content="data.feedbackMessage"
                      :repliable="true"
                      :hideableBox="false"
                      @reply="doSendReply($event)"/>
                  <div v-for="(r, idx) in firstLevelReplies" :key="r.id">
                    <v-divider class="my-1" v-show="idx < firstLevelReplies.length"></v-divider>
                    <MessageReply
                        :author="r.user"
                        :created-on="r.createdOn"
                        :content="r.content"
                        :repliable="true"
                        :replies="secondLevelReplies(r.id)"
                        @reply="doSendReply($event, r.id)"/>
                  </div>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>
        </v-container>


      </div>
    </v-tab-item>
    <v-tab-item class="height85vh scrollable">
      <Inspector
          :model="data.model"
          :dataset="data.dataset"
          :originalData="originalData"
          :inputData="userData"
          :isMiniMode="true"
          @reset="resetInput"
      />
    </v-tab-item>
  </v-tabs>
  <div v-else>Feedback #{{ id }} non existent</div>
</template>

<script lang="ts">
import {Component, Prop, Vue} from "vue-property-decorator";
import {api} from "@/api";
import {readToken} from "@/store/main/getters";
import {commitAddNotification} from '@/store/main/mutations';
import Inspector from "./Inspector.vue";
import MessageReply from "@/components/MessageReply.vue";
import {FeedbackDTO} from "@/generated-sources";

@Component({
  components: {Inspector, MessageReply}
})
export default class FeedbackDetail extends Vue {
  @Prop({required: true}) id!: number;

  data: FeedbackDTO | null = null;
  userData: object | null = null;
  originalData: object | null = null;

  async mounted() {
    await this.reloadFeedback()
  }

  async reloadFeedback() {
    try {
      this.data = (await api.getFeedback(this.id));
      this.userData = JSON.parse(this.data.userData);
      this.originalData = JSON.parse(this.data.originalData);
    } catch (error) {
      commitAddNotification(this.$store, {content: error.response.data.detail, color: 'error'});
    }
  }

  resetInput() {
    if (this.data) {
      this.userData = {...this.originalData}
    }
  }

  get firstLevelReplies() {
    return !this.data ? [] : this.data.feedbackReplies.filter(r => !r.replyToReply)
  }

  get secondLevelReplies() {
    return (replyId) => !this.data ? [] : this.data.feedbackReplies.filter(r => r.replyToReply == replyId)
  }

  async doSendReply(content: string, replyToId: number | null = null) {
    try {
      await api.replyToFeedback(this.id, content, replyToId)
      await this.reloadFeedback()
    } catch (error) {
      commitAddNotification(this.$store, {content: error.response.statusText, color: 'error'});
    }
  }
}
</script>

<style lang="scss" scoped>
.w100 {
  width: 100%;
  max-width: 100%;
}

.metadata {
  .caption {
    margin-bottom: 0;
  }

  .subtitle-2 {
    margin-bottom: 12px;
  }
}

div.height85vh {
  height: 85vh;
}

div.max75vh {
  max-height: 75vh;
}

div.scrollable {
  overflow-y: auto;
}
</style>
