<template>
  <vue-final-modal v-slot="{ close }" v-bind="$attrs" classes="modal-container" content-class="modal-content" v-on="$listeners">
    <div>
      <v-card>
        <v-card-title>
          Export Test Suite
          <v-spacer></v-spacer>
          <v-btn text href="https://docs.giskard.ai/en/latest/" target="_blank">
            <span>Documentation</span>
            <v-icon right>mdi-open-in-new</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-text>
          <CodeSnippet :codeContent="codeContent" :language="'python'"></CodeSnippet>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text class="mr-2 mb-2" color="primary" @click="close">Close</v-btn>
        </v-card-actions>
      </v-card>
    </div>
  </vue-final-modal>
</template>

<script lang="ts" setup>
import CodeSnippet from '@/components/CodeSnippet.vue';

const codeContent = `import giskard`;
</script>

<style scoped>
::v-deep(.modal-container) {
  height: 100%;
  padding: 0;
  margin: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow-y: auto;
}

::v-deep(.modal-content) {
  width: 80vw;
  height: fit-content;
}
</style>