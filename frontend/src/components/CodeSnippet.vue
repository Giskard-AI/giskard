<script setup lang="ts">
import { ref } from "vue";
import hljs from "highlight.js";
import "highlight.js/styles/github.css";
import { copyToClipboard } from "@/global-keys";


interface Props {
  codeContent?: string;
  language?: string;
}

const props = withDefaults(defineProps<Props>(), {
  codeContent: `# Code goes here
  def hello_world():
    print("Hello World!")`,
  language: 'python'
});

const highlightedCode = hljs.highlight(props.language, props.codeContent).value;

const copied = ref<boolean>(false);

async function copyCode() {
  await copyToClipboard(props.codeContent);
  copied.value = true;
  setTimeout(() => {
    copied.value = false;
  }, 2000);
}
</script>

<template>
  <!-- //NOSONAR -->
  <div class="pre-block rounded pa-4"><code v-html="highlightedCode" class="code-block" />
    <v-btn class="copy-button" small icon @click="copyCode">
      <v-icon small>mdi-content-copy</v-icon>
      <span v-show="copied" class="copied-message">Copied</span>
    </v-btn>
  </div>
</template>

<style scoped>
.pre-block {
  background-color: #F4F4F4;
  position: relative;
}

.code-block {
  background-color: #F4F4F4 !important;
  font-family: 'Roboto Mono', monospace;
  padding-left: 0;
  overflow-wrap: break-word;
  white-space: pre-wrap;
  font-size: 0.8rem;
}

.copy-button {
  position: absolute;
  right: 1rem;
  top: 1rem;
}

.copied-message {
  position: absolute;
  right: 2rem;
  top: 0.1rem;
  background-color: #176F38;
  color: #fff;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.7rem;
  font-weight: bold;
  font-family: Arial, Helvetica, sans-serif;
}
</style>
