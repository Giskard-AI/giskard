<script setup lang="ts">
import { ref } from 'vue'
const step = ref(1)

const emit = defineEmits(['close'])

const close = () => {
  emit('close')
  step.value = 1
}
</script>

<template>
  <v-stepper v-model="step" flat>
    <v-stepper-header id="stepper-header">
      <v-stepper-step :complete="step > 1" step="1">Start ML Worker</v-stepper-step>
      <v-divider></v-divider>
      <v-stepper-step :complete="step > 2" step="2">Create Giskard client</v-stepper-step>
      <v-divider></v-divider>
      <v-stepper-step :complete="step > 3" step="3">Create Giskard artifacts</v-stepper-step>
      <v-divider></v-divider>
      <v-stepper-step step="4">Upload test suite</v-stepper-step>
    </v-stepper-header>

    <v-stepper-items>
      <v-stepper-content step="1">
        <v-card class="mb-5" color="grey lighten-1" height="200px"></v-card>
        <v-btn color="primary" @click="step = 2">Continue</v-btn>
        <v-btn class="ml-2" @click="close" flat>Cancel</v-btn>
      </v-stepper-content>

      <v-stepper-content step="2">
        <v-card class="mb-5" color="grey lighten-1" height="200px"></v-card>
        <v-btn color="primary" @click="step = 3">Continue</v-btn>
        <v-btn class="ml-2" @click="close" flat>Cancel</v-btn>
      </v-stepper-content>

      <v-stepper-content step="3">
        <v-card class="mb-5" color="grey lighten-1" height="200px"></v-card>
        <v-btn color="primary" @click="step = 4">Continue</v-btn>
        <v-btn class="ml-2" @click="close" flat>Cancel</v-btn>
      </v-stepper-content>

      <v-stepper-content step="4">
        <v-card class="mb-5" color="grey lighten-1" height="200px"></v-card>
        <v-btn color="primary" @click="close">Close</v-btn>
        <v-btn class="ml-2" @click="step = 1" flat>Restart</v-btn>
      </v-stepper-content>
    </v-stepper-items>
  </v-stepper>
</template>

<style scoped>
#stepper-header {
  background-color: transparent;
  box-shadow: none !important;
}

.v-btn {
  margin-bottom: 0.5rem;
}
</style>