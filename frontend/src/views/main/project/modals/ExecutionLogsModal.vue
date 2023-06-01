<template>
  <vue-final-modal
      v-slot="{ close }"
      v-bind="$attrs"
      classes="modal-container"
      content-class="modal-content"
      v-on="$listeners"
  >
    <div class="text-center">
      <v-card>
        <v-card-title>
          Execution logs
        </v-card-title>
        <v-card-text>
          <pre class="logs caption pt-5">{{ props.logs }}</pre>
        </v-card-text>
        <v-card-actions>
          <v-btn color="secondary" @click="copyLogs">
            <v-icon>content_copy</v-icon>
            Copy logs
          </v-btn>
          <v-btn color="primary" @click="close">Close</v-btn>
        </v-card-actions>
      </v-card>
    </div>
  </vue-final-modal>
</template>

<script setup lang="ts">

import {useMainStore} from '@/stores/main';
import {copyToClipboard} from '@/global-keys';
import {TYPE} from "vue-toastification";

const props = (defineProps<{
  logs: string,
}>());


const mainStore = useMainStore()

async function copyLogs() {
    await copyToClipboard(props.logs);
    mainStore.addNotification({content: "Copied to clipboard", color: TYPE.SUCCESS});
}

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
  min-width: 50vw;
  max-width: 80vw;
  max-height: 80vh;
  overflow: auto;
}

.logs {
  white-space: pre-wrap;
  text-align: start;
}
</style>
