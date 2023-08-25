<template>
  <v-card>
    <v-card-title>
      Running on Hugging Face Spaces
    </v-card-title>
    <v-card-text>
      <p>Giskard Client and ML Worker need a Hugging Face access token to access your private Hugging Face Spaces.</p>
      <p>Access your <a href="https://huggingface.co/settings/tokens" target=”_blank”>Hugging Face settings</a> to get one.</p>

      <ValidationProvider name="Hugging Face access token" mode="eager" rules="required|min:30" v-slot="{errors}">
        <v-text-field outlined autofocus v-model="hfAccessToken" label="Hugging Face access token" type="text" :error-messages="errors"/>
      </ValidationProvider>

      See <a href="https://huggingface.co/docs/hub/security-tokens#user-access-tokens" target=”_blank”>Hugging Face docs</a> for more information.
    </v-card-text>
    <v-card-actions>
      <v-spacer></v-spacer>
      <v-btn color="accent" text @click="$emit('submit', hfAccessToken);">
        Fetch
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">

import { ref } from "vue";

const hfAccessToken = ref<string>("");

</script>
