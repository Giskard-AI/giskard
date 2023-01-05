<template>
  <div>
    <div>
      <span class="subtitle-2">{{ isCurrentUser ? 'me' : (author.displayName || author.user_id) }}</span>
      <span class="caption font-weight-light mx-2">{{ createdOn | date }}</span>
    </div>
    <div style="white-space: break-spaces">{{ content }}</div>
    <div v-if="replies">
      <div v-for="r in replies" :key="r.id" class="indented my-1">
        <message-reply :author="r.user" :createdOn="r.createdOn" :content="r.content"></message-reply>
      </div>
    </div>
    <div v-if="repliable" class="my-1" :class="{'indented': replies && replies.length}">
      <v-btn icon small @click="replyBoxToggle = !replyBoxToggle; reply = ''">
        <v-icon v-if="!openReplyBox" color="primary">mdi-reply</v-icon>
        <v-icon v-else color="accent" :disabled="!reply && !hideableBox">mdi-close</v-icon>
      </v-btn>
      <v-btn icon small color="primary" v-if="openReplyBox" :disabled="!reply" @click="emitSendReply">
        <v-icon>mdi-send</v-icon>
      </v-btn>
      <v-textarea
          v-if="openReplyBox"
          v-model="reply"
          placeholder="Add a reply..."
          rows=1
          class="mb-2"
          no-resize
          outlined
          hide-details
      ></v-textarea>
    </div>
  </div>
</template>

<script setup lang="ts">
import {computed, ref} from "vue";
import {useUserStore} from "@/stores/user";

const userStore = useUserStore();

interface Props {
  author: any,
  createdOn: string,
  content: string,
  repliable: boolean,
  hideableBox: boolean,
  replies: any[]
}

const props = defineProps<Props>();
const emit = defineEmits(["reply"])

const replyBoxToggle = ref<boolean>(false);
const reply = ref<string>("");

const isCurrentUser = computed(() => {
  return userStore.userProfile!.user_id === props.author.user_id;
});

const openReplyBox = computed(() => {
  return !props.hideableBox || replyBoxToggle.value;
});

function emitSendReply() {
  emit('reply', reply.value);
  reply.value = '';
  replyBoxToggle.value = false;
}
</script>

<style>
div.indented {
  margin-left: 5%
}
</style>