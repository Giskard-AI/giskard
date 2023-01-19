<template>
  <v-card>
    <v-card-title>Plan upgrade</v-card-title>
    <v-card-text>
      <span>TODO: Put an iframe here</span>
    </v-card-text>
    <v-card-actions>
      <v-spacer/>
      <v-btn small color="primary" @click="openFileInput">Upload license file</v-btn>
      <input type="file" ref="fileInput" style="display: none;" @change="onFileUpdate"/>
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
import {ref} from "vue";
import {api} from "@/api";

const fileInput = ref<any | null>(null);

function openFileInput() {
  fileInput.value?.click();
}

async function onFileUpdate(event) {
  let formData = new FormData();
  formData.append('file', event.target.files[0]);

  await api.uploadLicense(formData);
}

</script>

<style scoped>

</style>