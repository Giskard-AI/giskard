<template>
  <v-tabs v-if="data">
    <v-tab>Overview</v-tab>
    <v-tab @change="onInspectorActivated">Debugger</v-tab>
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
                      <div class='subtitle-2'>{{ userDisplayName }}</div>
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
                  <MessageReply :replyId="data.id" :author="data.user" :created-on="data.createdOn" :content="data.feedbackMessage" :repliable="true" :replies=firstLevelReplies :type="'feedback'" :hideableBox="false" @reply="doSendReply($event)" @delete="deleteFeedback" />
                  <div v-for="(r, idx) in firstLevelReplies" :key="r.id">
                    <v-divider class="my-1" v-show="idx < firstLevelReplies.length"></v-divider>
                    <MessageReply :replyId="r.id" :author="r.user" :created-on="r.createdOn" :content="r.content" :repliable="true" :replies="secondLevelReplies(r.id)" :type="'reply'" @reply="doSendReply($event, r.id)" @delete="deleteReply" :hideableBox="false" />
                  </div>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>
        </v-container>


      </div>
    </v-tab-item>
    <v-tab-item class="height85vh scrollable">
      <Inspector :model="data.model" :dataset="data.dataset" :originalData="originalData" :inputData="userData" :isMiniMode="true" @reset="resetInput" />
    </v-tab-item>
  </v-tabs>
  <div v-else>Feedback #{{ id }} non existent</div>
</template>

<script setup lang="ts">
import { api } from '@/api';
import Inspector from './Inspector.vue';
import MessageReply from '@/components/MessageReply.vue';
import { FeedbackDTO, FeedbackReplyDTO } from '@/generated-sources';
import mixpanel from 'mixpanel-browser';
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { $vfm } from 'vue-final-modal';
import ConfirmModal from '@/views/main/project/modals/ConfirmModal.vue';
import { useMainStore } from '@/stores/main';

const mainStore = useMainStore();

const router = useRouter();

interface Props {
  id: number,
}

const props = defineProps<Props>();

const data = ref<FeedbackDTO | null>(null);
const userData = ref<{ [key: string]: string } | null>(null);
const originalData = ref<object | null>(null);
onMounted(() => {
  reloadFeedback();
})

async function reloadFeedback() {
  data.value = (await api.getFeedback(props.id));
  userData.value = JSON.parse(data.value.userData);
  originalData.value = JSON.parse(data.value.originalData);
}

function onInspectorActivated() {
  mixpanel.track('Open inspector from feedback', {
    modelId: data.value?.model.id,
    datasetId: data.value?.dataset.id
  });
}

function resetInput() {
  if (data.value) {
    userData.value = { ...originalData.value }
  }
}

async function doSendReply(content: string, replyToId: number | null = null) {
  mixpanel.track('Reply to feedback', { replyTo: replyToId });
  await api.replyToFeedback(props.id, content, replyToId);
  await reloadFeedback();
  mainStore.addSimpleNotification('Reply sent!');
}

function deleteFeedback(feedbackId: number) {
  $vfm.show({
    component: ConfirmModal,
    bind: {
      title: 'Delete feedback',
      text: `Are you sure that you want to delete this feedback permanently? All replies will be deleted as well.`,
      isWarning: true
    },
    on: {
      async confirm(close) {
        await api.deleteFeedback(feedbackId);
        await router.push({ name: 'project-feedback', params: { id: data.value!.project.id.toString() } });
        close();
        mainStore.addSimpleNotification('Successfully deleted feedback!');
      }
    }
  });
}

function deleteReply(replyId: number) {
  $vfm.show({
    component: ConfirmModal,
    bind: {
      title: 'Delete reply',
      text: `Are you sure that you want to delete this reply permanently? All replies to this reply will be deleted as well.`,
      isWarning: true
    },
    on: {
      async confirm(close) {
        await api.deleteFeedbackReply(data.value!.id, replyId);
        await reloadFeedback();
        close();
        mainStore.addSimpleNotification('Successfully deleted reply!');
      }
    }
  });
}

const firstLevelReplies = computed<FeedbackReplyDTO[]>(() => {
  return !data.value ? [] : data.value.feedbackReplies.filter(r => !r.replyToReply);
});

function secondLevelReplies(replyId: number) {
  return !data.value ? [] : data.value.feedbackReplies.filter(r => r.replyToReply === replyId);
}

const userDisplayName = computed(() => data.value?.user
  ? data.value.user.displayName ?? data.value.user.user_id
  : 'Deleted user');

</script>

<style lang="scss" scoped>
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
