<template>
  <v-card>
    <v-card-title>Plan upgrade</v-card-title>
    <v-card-text>
      If you bought an upgraded license plan, you can upload your new license file here.
      <!-- This is where an embed with available license plans could go ? -->
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
import {useMainStore} from "@/stores/main";

const mainStore = useMainStore();

const emit = defineEmits(['done']);
const fileInput = ref<any | null>(null);

function openFileInput() {
  fileInput.value?.click();
}

async function onFileUpdate(event) {
  let formData = new FormData();
  formData.append('file', event.target.files[0]);

  await api.uploadLicense(formData);
  await mainStore.fetchAppSettings();
  await mainStore.fetchLicense();
  mainStore.addSimpleNotification("License file uploaded. You may need to refresh the page to see new features.")
  emit('done');
}

</script>

<style scoped>

</style>