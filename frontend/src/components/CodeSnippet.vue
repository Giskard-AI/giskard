<script setup lang="ts">
import hljs from "highlight.js";
import "highlight.js/styles/github.css";

interface Props {
  codeContent: string;
  language: string;
}

const props = withDefaults(defineProps<Props>(), {
  codeContent: '# Code goes here',
  language: 'python'
});

const highlightedCode = hljs.highlight(props.language, props.codeContent).value;
</script>

<template>
  <pre class="pre-block rounded pa-4"><code v-html="highlightedCode" class="code-block"></code></pre>
</template>

<style scoped>
.pre-block {
  background-color: #F4F4F4;
}

.code-block {
  background-color: #F4F4F4 !important;
  font-style: normal;
  font-weight: 500;
}
</style>