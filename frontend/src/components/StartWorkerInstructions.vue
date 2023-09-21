<template>
  <v-card outlined v-if="needFetchWithHFAccessToken === false" :loading="isLoading">
    <v-skeleton-loader v-if="isLoading" type="card" />
    <template v-else>
      <v-card-text v-if="apiKeyStore.getFirstApiKey">
        <v-alert class="pa-0 text-body-2" colored-border type="info">
          <p class="mb-0">ML Worker is a python process that allows Giskard to execute models in a user's
            environment</p>
          <p v-if="appSettings">A worker communicates with the backend through WebSocket. Make sure that
            your worker machine can access the Giskard server machine.
          </p>
        </v-alert>
        <div>
          <p>To connect a worker, install giskard library in any code environment of your choice with</p>
          <CodeSnippet codeContent='pip install "giskard>=2.0.0b" -U' />
          <p class="mt-4 mb-4">then run the following command to connect to this Giskard server:</p>
          <CodeSnippet :codeContent="codeContent" />
          <p class="mt-4" v-if="route.name !== 'admin-general'">You can check the status of an ML Worker and
            generate a new API token on the
            <router-link :to="{ name: 'admin-general' }">Settings</router-link>
            page
          </p>
        </div>
      </v-card-text>
      <v-card-text v-else>
        <v-row>
          <v-col>
            <p class="mb-0">You need to add an API key to connect an ML Worker</p>
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-btn @click="apiKeyStore.create()">Create API Key</v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </template>
  </v-card>
  <HuggingFaceTokenCard v-else-if="needFetchWithHFAccessToken" @submit="fetchAndSaveHFSpacesTokenWithAccessToken" />
  <LoadingFullscreen v-else :name="'MLWorker instructions'" />
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useMainStore } from "@/stores/main";
import { useRoute } from "vue-router/composables";
import { apiURL } from "@/env";
import CodeSnippet from "./CodeSnippet.vue";
import { saveLocalHFToken } from "@/utils";
import HuggingFaceTokenCard from "./HuggingFaceTokenCard.vue";
import LoadingFullscreen from "./LoadingFullscreen.vue";
import { TYPE } from 'vue-toastification';
import { useApiKeyStore } from "@/stores/api-key-store";
import { useHFSpacesTokenStore } from "@/stores/hfspaces";

const appSettings = computed(() => mainStore.appSettings);

const mainStore = useMainStore();
const apiKeyStore = useApiKeyStore();
const route = useRoute();


const needFetchWithHFAccessToken = ref<boolean | null>(null);

const hfToken = ref<string | null>(null);
const isLoading = ref<boolean>(true);

const codeContent = computed(() => {
  if (mainStore.appSettings!.isRunningOnHfSpaces && hfToken.value) {
    try {
      return `giskard worker start -u ${apiURL} -k ${apiKeyStore.getFirstApiKey} --hf-token ${hfToken.value}`;
    } catch (error) {
      console.error(error);
    }
  }
  return `giskard worker start -u ${apiURL} -k ${apiKeyStore.getFirstApiKey}`;
});

async function fetchAndSaveHFSpacesTokenWithAccessToken(accessToken: string) {
  if (mainStore.appSettings!.isRunningOnHfSpaces) {
    saveLocalHFToken(accessToken);

    const hfSpacesTokenStore = useHFSpacesTokenStore();
    const token = await hfSpacesTokenStore.getHFSpacesToken();
    if (token === null) {
      // Private HFSpaces or no valid HF access token
      needFetchWithHFAccessToken.value = true;
      mainStore.addNotification({ content: 'Invalid Hugging Face access token', color: TYPE.ERROR });
    } else if (!hfSpacesTokenStore.publicSpace) {
      needFetchWithHFAccessToken.value = false;
      hfToken.value = token;
    }
  }
}

async function generateHFSpacesToken() {
  if (mainStore.appSettings?.isRunningOnHfSpaces) {
    const hfSpacesTokenStore = useHFSpacesTokenStore();
    const token = await hfSpacesTokenStore.getHFSpacesToken();
    if (token === null) {
      // Private HFSpaces or no valid HF access token
      needFetchWithHFAccessToken.value = true;
      return;
    } else if (!hfSpacesTokenStore.publicSpace) {
      hfToken.value = token;
    }
    needFetchWithHFAccessToken.value = false;
  }
}

onMounted(async () => {

  await apiKeyStore.getAll();
  if (mainStore.appSettings!.isRunningOnHfSpaces) {
    await generateHFSpacesToken();
  } else {
    needFetchWithHFAccessToken.value = false;
  }
  isLoading.value = false;
})
</script>
