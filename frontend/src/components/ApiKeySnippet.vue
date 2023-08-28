<script lang="ts" setup>
import {computed, ref} from "vue";
import {copyToClipboard} from "@/global-keys";

import "highlight.js/styles/stackoverflow-light.css";

import python from 'highlight.js/lib/languages/python';
import json from 'highlight.js/lib/languages/json';
import bash from 'highlight.js/lib/languages/bash';
import plaintext from 'highlight.js/lib/languages/plaintext';
import hljs from "highlight.js";


const props = withDefaults(defineProps<{
  code: string;
  masked?: boolean;
  unmaskedChars?: number
  language?: 'python' | 'bash' | 'json' | 'plaintext';
}>(), {
  language: 'plaintext',
  masked: false,
  unmaskedChars: 6
});

const copied = ref<boolean>(false);
const isShown = ref<boolean>(false);

async function showCode() {
  isShown.value = !isShown.value;
}

async function copyCode() {
  await copyToClipboard(props.code);
  copied.value = true;
  setTimeout(() => {
    copied.value = false;
  }, 2000);
}

const code = computed(() => {
  const clear = props.code;
  if (props.masked && !isShown.value) {
    return clear.substring(0, props.unmaskedChars) + '*'.repeat(3) + clear.substring(clear.length - props.unmaskedChars);
  }
  return clear;
});
const highlightedCode = computed(() => {
  return hljs.highlight(props.language, code.value).value;
});

</script>

<template>
  <div class="main-container">
    <!-- //NOSONAR --><code v-html="highlightedCode" class="code-block"/>

    <div class="controls">
      <span class="copied-message" v-show="copied">Copied</span>
      <v-icon v-if="props.masked" class="copy-button copy-btn mr-3" size="20px" @click="showCode">
        {{ isShown ? 'mdi-eye-off' : 'mdi-eye' }}
      </v-icon>
      <v-icon class="copy-button copy-btn" size="20px" @click="copyCode">mdi-content-copy</v-icon>
    </div>
  </div>
</template>

<style scoped>
.copy-btn {
  color: rgb(36, 41, 46);
}

.main-container {
  position: relative;
}

.controls {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  right: 5px;
}

.copied-message {
  margin-right: 0.5rem;
  background-color: #176F38;
  color: #fff;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-weight: bold;
}

.code-block {
  font-size: medium;
  display: block;
  padding-right: 2.5em;
}

.masked .code-block {
  padding-right: 4em;
}

</style>
