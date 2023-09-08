<template>
  <v-card height="100%">
    <v-card-title class="font-weight-light secondary--text">Create a Giskard Client</v-card-title>
    <v-card-text v-if="giskardClientTemplate != null">
      <CodeSnippet :code-content="giskardClientTemplate"/>
    </v-card-text>
    <v-card-text v-else-if="needFetchWithHFAccessToken == null">
      <LoadingFullscreen :name="'Giskard Client creating instructions'"/>
    </v-card-text>
    <v-card-text v-else-if="!state.workerStatus.connected && !props.internalHFAccessToken">
      <div class="mb-2">
        <v-btn small tile color="primaryLight" class="primaryLightBtn" @click="generateHFToken">Generate</v-btn>
      </div>
      <v-row>
        <v-col>
          Please enter your Hugging Face access token in Giskard Settings page to generate the instructions.
        </v-col>
      </v-row>
    </v-card-text>
    <v-card-text v-else>
      <HuggingFaceTokenCard @submit="fetchAndSaveHFSpacesTokenWithAccessToken"/>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useMainStore } from "@/stores/main";
import { TYPE } from "vue-toastification";

import CodeSnippet from "@/components/CodeSnippet.vue";
import LoadingFullscreen from "./LoadingFullscreen.vue";
import HuggingFaceTokenCard from "./HuggingFaceTokenCard.vue";

import { saveLocalHFToken, getLocalHFToken } from "@/utils";
import { attemptFetchHFSpacesToken } from "@/hf-utils";

import { apiURL } from "@/env";
import { state } from "@/socket";

import { JWTToken } from "@/generated-sources";
import { api } from "@/api";

import { useApiKeyStore } from "@/stores/api-key-store";

const apiKeyStore = useApiKeyStore();
const mainStore = useMainStore();

interface Props {
  internalHFAccessToken: boolean,
}

const props = withDefaults(defineProps<Props>(), {
  internalHFAccessToken: false,
});

function generateGiskardClientInstruction(hf_token=null) {
  let snippet = `from giskard import GiskardClient

url = "${apiURL}"
api_token = "${apiKeyStore.getFirstApiKey ? apiKeyStore.getFirstApiKey : '<Generate your API Key first>'}"
`;
  if (hf_token) {
    snippet += `hf_token = "${hf_token}"
`;
  }
  snippet += `
# Create a giskard client to communicate with Giskard
client = GiskardClient(url, api_token`;
  if (hf_token) {
    snippet += `, hf_token`;
  }
  snippet += `)`;
  return snippet;
};

// Hugging Face Spaces token (Giskard Space token)
const giskardClientTemplate = ref<string | null>(null);
const needFetchWithHFAccessToken = ref<boolean | null>(null);

async function fetchAndSaveHFSpacesTokenWithAccessToken(accessToken: string) {
  if (mainStore.appSettings!.isRunningOnHfSpaces) {
    saveLocalHFToken(accessToken);
    await attemptFetchHFSpacesToken((token) => {
      giskardClientTemplate.value = generateGiskardClientInstruction(token);
      needFetchWithHFAccessToken.value = false;
    }, () => {
      needFetchWithHFAccessToken.value = true;
      mainStore.addNotification({content: 'Invalid Hugging Face access token', color: TYPE.ERROR});
    });
  }
}

async function generateHFToken() {
  if (mainStore.appSettings?.isRunningOnHfSpaces) {
    attemptFetchHFSpacesToken((token) => {
      if (getLocalHFToken() === null) token = null; // For public space, not necessary
      giskardClientTemplate.value = generateGiskardClientInstruction(token);
      needFetchWithHFAccessToken.value = false;
    }, () => {
      // Access Token seems invalidated or private Hugging Face Spaces
      needFetchWithHFAccessToken.value = true;
    });
  }
}

onMounted(() => {
  if (mainStore.appSettings?.isRunningOnHfSpaces) {
    generateHFToken();
  } else {
    needFetchWithHFAccessToken.value = false;
    giskardClientTemplate.value = generateGiskardClientInstruction();
  }
});

</script>
  