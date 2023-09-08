<template>
  <v-card height="100%" class="d-flex flex-column">
    <v-card-title class="font-weight-light secondary--text">API Keys</v-card-title>
    <v-card-text class="flex-grow-1 d-flex flex-column">
      <div class="mb-2">
        <v-btn small tile color="primaryLight" class="primaryLightBtn text-right" @click="generateToken">Generate</v-btn>
      </div>
      <div class="flex-grow-1 overflow-x-hidden" style="max-height:170px">
        <v-row v-for="key in apiKeyStore.apiKeys" dense>
          <v-col>
            <ApiKeySnippet :code="key.key" masked/>
          </v-col>
          <v-col cols="1">
            <v-btn icon @click="deleteApiKey(key)" :disabled="apiKeyStore.apiKeys.length == 1">
              <v-icon>mdi-delete</v-icon>
            </v-btn>
          </v-col>
        </v-row>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import {onMounted, ref} from "vue";
import {JWTToken} from "@/generated-sources";
import {useMainStore} from "@/stores/main";
import {useApiKeyStore} from "@/stores/api-key-store";
import ApiKeySnippet from "@/components/ApiKeySnippet.vue";

const mainStore = useMainStore();
const apiKeyStore = useApiKeyStore();

const apiAccessToken = ref<JWTToken | null>(null);

async function generateToken() {
  const loadingNotification = {content: 'Generating...', showProgress: true};
  mainStore.addNotification(loadingNotification);
  mainStore.removeNotification(loadingNotification);
  await apiKeyStore.create();
}

async function deleteApiKey(key) {
  await apiKeyStore.delete(key.id);
}

onMounted(async () => await apiKeyStore.getAll())
</script>
