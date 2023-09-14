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
import { useHFSpacesTokenStore } from "@/stores/hfspaces";

import { apiURL } from "@/env";
import { state } from "@/socket";

import { useApiKeyStore } from "@/stores/api-key-store";

const apiKeyStore = useApiKeyStore();
const mainStore = useMainStore();

interface Props {
  internalHFAccessToken: boolean,
}

const props = withDefaults(defineProps<Props>(), {
  internalHFAccessToken: false,
});

function generateGiskardClientInstruction(hf_token: string | null = null) {
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
    const hfSpacesTokenStore = useHFSpacesTokenStore();
    const token = await hfSpacesTokenStore.getHFSpacesToken();
    if (token === null) {
      needFetchWithHFAccessToken.value = true;
      mainStore.addNotification({content: 'Invalid Hugging Face access token', color: TYPE.ERROR});
    } else {
      giskardClientTemplate.value = generateGiskardClientInstruction(token);
      needFetchWithHFAccessToken.value = false;
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
    } else if (!hfSpacesTokenStore.publicSpace) {
      needFetchWithHFAccessToken.value = false;
      giskardClientTemplate.value = generateGiskardClientInstruction(token);
    }
  }
}

onMounted(async () => {
  if (mainStore.appSettings?.isRunningOnHfSpaces) {
    await generateHFSpacesToken();
  } else {
    needFetchWithHFAccessToken.value = false;
    giskardClientTemplate.value = generateGiskardClientInstruction();
  }
});

</script>
  
