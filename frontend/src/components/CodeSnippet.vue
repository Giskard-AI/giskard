<script setup lang="ts">
import hljs from "highlight.js";
import "highlight.js/styles/github.css";
import { copyToClipboard } from "@/global-keys";


interface Props {
  codeContent: string;
  language: string;
}

const props = withDefaults(defineProps<Props>(), {
  codeContent: '# Code goes here',
  language: 'python'
});

const highlightedCode = hljs.highlight(props.language, props.codeContent).value;

async function copyCode() {
  await copyToClipboard(props.codeContent);
}
</script>

<template>
  <pre class="pre-block rounded pa-4">
    <code v-html="highlightedCode" class="code-block"></code><v-btn class="copy-button" small icon @click="copyCode"><v-icon small>mdi-content-copy</v-icon></v-btn>
  </pre>
</template>

<style scoped>
.pre-block {
  background-color: #F4F4F4;
  position: relative;
}

.code-block {
  background-color: #F4F4F4 !important;
  font-style: normal;
  font-weight: 500;
}

.copy-button {
  position: absolute;
  right: 1rem;
  top: 1rem;
}
</style>