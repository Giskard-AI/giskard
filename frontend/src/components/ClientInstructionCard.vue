<template>
  <v-card height="100%">
    <v-card-title class="font-weight-light secondary--text">Create a Giskard Client</v-card-title>
    <v-card-text>
      <CodeSnippet :code-content="giskardClientTemplate"/>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useMainStore } from "@/stores/main";
import CodeSnippet from "@/components/CodeSnippet.vue";

const mainStore = useMainStore();

const giskardClientTemplate = computed<string>(() => {
  let snippet = `from giskard import GiskardClient

url = "<Giskard instance URL>"  # you can find the URL of your Giskard instance in Application card in the Settings tab 
token = "<API Access Token>"    # you can generate your API Access token in the Settings tab of the Giskard application
`;
  if (mainStore.appSettings?.isRunningOnHfSpaces) {
    snippet += `hf_token = "<Giskard Space Token>"  # you can generate your Giskard Space token in the Settings tab of the Giskard application
`;
  }
  snippet += `
# Create a giskard client to communicate with Giskard
client = GiskardClient(url, token`;
  if (mainStore.appSettings?.isRunningOnHfSpaces) {
    snippet += `, hf_token`;
  }
  snippet += `);`;
  return snippet;
});

</script>
  