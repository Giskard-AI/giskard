<template>
  <div>
    <div class='d-flex'>
      <v-icon class='pb-1 mr-1' left>{{ icon }}</v-icon>
      <span>{{ title }}</span>
    </div>
    <CodeSnippet :codeContent="content" :language="'python'" class='mt-2'></CodeSnippet>
  </div>
</template>

<script setup lang="ts">

interface Props {
  title: string
  icon: string
  content: string
}

const props = defineProps<Props>();

import CodeSnippet from "@/components/CodeSnippet.vue";
</script>

<style scoped>
.v-icon {
  color: #087038;
  font-size: 1.25rem;
  margin-top: 0.3rem;
}

span {
  font-size: 1.25rem;
  font-weight: 500;
  letter-spacing: normal;
}
</style>

