<template>
  <v-tabs v-if="data">
    <v-tab>Overview</v-tab>
    <v-tab>Inspector</v-tab>
    <v-tab-item class="height85vh">
      <div fluid class="d-flex flex-column metadata fill-height align-baseline">
        <v-container class="w100 flex-grow-1 ">
          <v-row class="grow">
          <v-col md=5>
            <v-card class="scrollable max75vh">
              <v-card-text>
                <v-row>
                  <v-col>
                    <div class="caption font-weight-light">Originator</div>
                    <div class="subtitle-2">{{ data.user.display_name || data.user.user_id }}</div>
                    <div class="caption font-weight-light">Sent On</div>
                    <div class="subtitle-2">{{ new Date(data.created_on).toLocaleString() }}</div>
                    <div class="caption font-weight-light">Model</div>
                    <div class="subtitle-2">{{ data.model.file_name }}</div>
                    <div class="caption font-weight-light">Dataset File</div>
                    <div class="subtitle-2">{{ data.dataset.file_name }}</div>
                  </v-col>
                  <v-col>
                    <div class="caption font-weight-light">Feedback Type</div>
                    <div class="subtitle-2">{{ data.feedback_type }}</div>
                    <div class="caption font-weight-light">Feedback Choice</div>
                    <div class="subtitle-2">{{ data.feedback_choice }}</div>
                    <div class="caption font-weight-light">Feature</div>
                    <div class="subtitle-2">{{ data.feature_name || "-" }}</div>
                    <div class="caption font-weight-light">Feature Value</div>
                    <div class="subtitle-2">{{ data.feature_value || "-" }}</div>
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
                    :created_on="data.created_on"
                    :content="data.feedback_message"
                    :repliable="true"
                    :hideableBox="false"
                    @reply="doSendReply($event)"/>
                <div v-for="(r, idx) in firstLevelReplies" :key="r.id">
                  <v-divider class="my-1" v-show="idx < firstLevelReplies.length"></v-divider>
                  <MessageReply
                      :author="r.user"
                      :created_on="r.created_on"
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
          :modelId="data.model.id"
          :datasetId="data.dataset.id"
          :originalData="data.original_data"
          :inputData="data.user_data"
          :targetFeature="data.target_feature"
          :isMiniMode="true"
          @reset="resetInput"
      />
    </v-tab-item>
  </v-tabs>
  <div v-else>Feedback #{{ id }} non existent</div>
</template>

<script lang="ts">
import {Component, Vue, Prop} from "vue-property-decorator";
import {api} from "@/api";
import {readToken} from "@/store/main/getters";
import {commitAddNotification} from '@/store/main/mutations';
import {IFeedbackDisplay} from "@/interfaces";
import Inspector from "./Inspector.vue";
import MessageReply from "@/components/MessageReply.vue";

@Component({
  components: {Inspector, MessageReply}
})
export default class FeedbackDetail extends Vue {
  @Prop({required: true}) id!: number;

  data: IFeedbackDisplay | null = null;
  replyPlaceholder = ""

  async mounted() {
    await this.reloadFeedback()
  }

  async reloadFeedback() {
    try {
      const response = await api.getFeedback(readToken(this.$store), this.id);
      this.data = response.data
    } catch (error) {
      commitAddNotification(this.$store, {content: error.response.data.detail, color: 'error'});
    }
  }

  resetInput() {
    if (this.data) this.data.user_data = {...this.data?.original_data}
  }

  get firstLevelReplies() {
    return !this.data ? [] : this.data.replies.filter(r => !r.reply_to_reply)
  }

  get secondLevelReplies() {
    return (replyId) => !this.data ? [] : this.data.replies.filter(r => r.reply_to_reply == replyId)
  }

  async doSendReply(content: string, replyToId: number | null = null) {
    try {
      await api.replyToFeedback(readToken(this.$store), this.id, content, replyToId)
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
    margin-bottom: 0px;
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
