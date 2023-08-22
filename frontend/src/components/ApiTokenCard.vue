<template>
  <v-card height="100%">
    <v-card-title class="font-weight-light secondary--text">API Access Token</v-card-title>
    <v-card-text>
      <div class="mb-2">
        <v-btn small tile color="primaryLight" class="primaryLightBtn" @click="generateToken">Generate</v-btn>
        <v-btn v-if="apiAccessToken && apiAccessToken.id_token" small tile color="secondary" class="ml-2" @click="copyToken">
          Copy
          <v-icon right dark>mdi-content-copy</v-icon>
        </v-btn>
      </div>
      <v-row>
        <v-col>
          <div class="token-area-wrapper" v-if="apiAccessToken && apiAccessToken.id_token">
            <CodeSnippet :code-content="apiAccessToken.id_token"/>
          </div>
        </v-col>
      </v-row>
      <v-row v-if="apiAccessToken && apiAccessToken.id_token">
        <v-col class="text-right">
          Expires on <span>{{ apiAccessToken.expiryDate | date }}</span>
        </v-col>
      </v-row>
    </v-card-text>
    <div v-if="hfSpacesToken != null">
      <v-card-title class="font-weight-light secondary--text">Giskard Space Token</v-card-title>
      <v-card-text>
        <div class="mb-2">
          <v-btn small tile color="primaryLight" class="primaryLightBtn" @click="generateHFToken">Generate</v-btn>
          <v-btn v-if="hfSpacesToken" small tile color="secondary" class="ml-2" @click="copyHFToken">
            Copy
            <v-icon right dark>mdi-content-copy</v-icon>
          </v-btn>
        </div>
        <v-row>
          <v-col>
            <div class="token-area-wrapper" v-if="hfSpacesToken">
              <CodeSnippet :code-content="hfSpacesToken"/>
            </div>
          </v-col>
        </v-row>
        <v-row v-if="hfSpacesToken">
          <v-col class="text-right">
            Expires on <span>{{ hfSpacesTokenExpiredDate.toLocaleString() }}</span>
          </v-col>
        </v-row>
      </v-card-text>
    </div>
  </v-card>
</template>

<script setup lang="ts">
import {ref} from "vue";
import {JWTToken} from "@/generated-sources";
import {api} from "@/api";
import {copyToClipboard} from "@/global-keys";
import {useMainStore} from "@/stores/main";
import {TYPE} from "vue-toastification";
import CodeSnippet from "@/components/CodeSnippet.vue";

import { attemptFetchHFSpacesToken, fetchHFSpacesToken } from "@/hf-utils";

const mainStore = useMainStore();

const apiAccessToken = ref<JWTToken | null>(null);

async function generateToken() {
  const loadingNotification = { content: 'Generating...', showProgress: true };
  try {
    apiAccessToken.value = null;  // Set token to null to force render of CodeSnippet

    mainStore.addNotification(loadingNotification);
    mainStore.removeNotification(loadingNotification);

    if (mainStore.appSettings?.isRunningOnHfSpaces && hfSpacesToken.value === null) {
      attemptFetchHFSpacesToken((token) => {
        hfSpacesToken.value = token;
        updateHFTokenExpiration();
      }, () => {
        // Error: do not show HF Spaces token for not
        hfSpacesToken.value = null;
      })
    }

    apiAccessToken.value = await api.getApiAccessToken();
  } catch (error) {
    mainStore.removeNotification(loadingNotification);
    mainStore.addNotification({content: 'Could not reach server', color: TYPE.ERROR});
  }
}

async function copyToken() {
  await copyToClipboard(apiAccessToken.value?.id_token);
  mainStore.addNotification({content: "Copied to clipboard", color: TYPE.SUCCESS});
}

const hfSpacesToken = ref<string | null>(null);
const hfSpacesTokenExpiredDate = ref<Date>(new Date());

function updateHFTokenExpiration() {
  hfSpacesTokenExpiredDate.value = new Date();
  hfSpacesTokenExpiredDate.value.setDate(hfSpacesTokenExpiredDate.value.getDate() + 1);
}

async function generateHFToken() {
  if (mainStore.appSettings?.isRunningOnHfSpaces) {
    hfSpacesToken.value = null;
    hfSpacesToken.value = await fetchHFSpacesToken();
    updateHFTokenExpiration();
  }
}

async function copyHFToken() {
  await copyToClipboard(hfSpacesToken.value);
  mainStore.addNotification({content: "Copied to clipboard", color: TYPE.SUCCESS});
}

</script>
