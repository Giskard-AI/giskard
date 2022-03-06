<template>
<div>
  <div>
    <span class="subtitle-2">{{isCurrentUser? 'me' : (author.display_name || author.user_id)}}</span>
    <span class="caption font-weight-light mx-2">{{new Date(created_on).toLocaleString()}}</span>
  </div>
  <div style="white-space: break-spaces">{{content}}</div>
  <div v-if="replies">
    <div v-for="r in replies" :key="r.id" class="indented my-1">
      <message-reply :author="r.user" :created_on="r.created_on" :content="r.content" ></message-reply>
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

<script>
import { readUserProfile } from '@/store/main/getters';

export default {
  name: 'message-reply',
  props: {
    author: {type: Object, required: true},
    created_on: {type: String, required: true},
    content: {type: String, required: true},
    repliable: {type: Boolean, default: false},
    hideableBox: {type: Boolean, default: true},
    replies: {type: Array}
  },
  data() {
    return {
      replyBoxToggle: false,
      reply: ''
    }
  },
  computed: {
    isCurrentUser: function() {
      return readUserProfile(this.$store).user_id == this.author.user_id
    },
    openReplyBox: function() {
      return !this.hideableBox || this.replyBoxToggle
    }
  },
  methods: {
    emitSendReply() {
      this.$emit('reply', this.reply)
      this.reply = ''
      this.replyBoxToggle = false
    }
  }
}
</script>    
<style>
div.indented {
  margin-left: 5%
}
</style>