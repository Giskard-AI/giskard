<template>
  <div>
    <div>
      <span class="subtitle-2">{{ isCurrentUser ? 'me' : (author.displayName || author.user_id) }}</span>
      <span class="caption font-weight-light mx-2">{{ createdOn | date }}</span>
      <v-btn icon small color="accent" v-if="isCurrentUser" @click="deleteReply(replyId)">
        <v-icon small>mdi-delete</v-icon>
      </v-btn>
    </div>
    <div style="white-space: break-spaces">{{ content }}</div>
    <div v-if="replies && type == 'reply'">
      <div v-for="r in replies" :key="r.id" class="indented my-1">
        <message-reply :replyId="r.id" :author="r.user" :createdOn="r.createdOn" :content="r.content" :type="'reply'" :repliable="false" :replies="[]" @delete="deleteReply(r.id)"></message-reply>
      </div>
    </div>
    <div v-if="repliable" class="my-1" :class="{ 'indented': replies && replies.length }">
      <v-textarea class="mb-2 reply-input" v-if="openReplyBox" v-model="reply" placeholder="Add a reply..." rows="1" no-resize outlined hide-details :clearable="false">
        <template v-slot:append v-if="reply">
          <v-btn icon small color="accent" @click="replyBoxToggle = !replyBoxToggle; reply = ''">
            <v-icon>mdi-close</v-icon>
          </v-btn>
          <v-btn icon small class="pl-1" color="primary" @click=" emitSendReply ">
            <v-icon>mdi-send</v-icon>
          </v-btn>
        </template>
      </v-textarea>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useUserStore } from "@/stores/user";

const userStore = useUserStore();

interface Props {
  replyId: number,
  type: string,
  author: any,
  createdOn: string,
  content: string,
  repliable: boolean,
  hideableBox: boolean,
  replies: any[]
}

const props = defineProps<Props>();
const emit = defineEmits(["reply", "delete"])

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

function deleteReply(id: number) {
  emit('delete', id);
}
</script>

<style>
div.indented {
  margin-left: 5%
}
</style>