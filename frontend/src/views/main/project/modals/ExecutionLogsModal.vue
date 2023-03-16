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
          <v-btn color="primary" @click="close">Close</v-btn>
        </v-card-actions>
      </v-card>
    </div>
  </vue-final-modal>
</template>

<script setup lang="ts">

const props = (defineProps<{
  logs: string,
}>());


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
  max-height: 80vh;
  overflow: auto;
}

.logs {
  text-align: start;
}
</style>
