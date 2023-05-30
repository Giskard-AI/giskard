<template>
  <vue-final-modal v-slot="{ close }" v-bind="$attrs" classes="modal-container" content-class="modal-content" v-on="$listeners">
    <div>
      <v-card>
        <v-card-title>
          {{ title }}
          <v-spacer></v-spacer>
          <v-btn text href="https://docs.giskard.ai/start/" target="_blank">
            <span>Documentation</span>
            <v-icon right>mdi-open-in-new</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-text>
          <CodeSnippet :code-content="codeContent" :language="'python'"></CodeSnippet>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text class="mr-2 mb-2" color="primary" @click="close">Close</v-btn>
        </v-card-actions>
      </v-card>
    </div>
  </vue-final-modal>
</template>

<script setup lang="ts">
import CodeSnippet from '@/components/CodeSnippet.vue';

interface Props {
  title: string,
  codeContent: string
}

const props = defineProps<Props>();
</script>

<style scoped>
::v-deep(.modal-container) {
  display: flex;
  justify-content: center;
  align-items: center;
}

::v-deep(.modal-content) {
  position: relative;
  display: flex;
  flex-direction: column;
  margin: 0 1rem;
  padding: 1rem;
}
</style>