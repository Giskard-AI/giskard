<script setup lang="ts">
import { onMounted, ref } from "vue";
import { api } from "@/api";
import { MLWorkerInfoDTO } from "@/generated-sources";
import CodeSnippet from "./CodeSnippet.vue";

const step = ref(1);
const toggleArtifactType = ref<string>("dataset");
const toggleTestType = ref<string>("scan");

const allMLWorkerSettings = ref<MLWorkerInfoDTO[]>([]);
const externalWorker = ref<MLWorkerInfoDTO | null>(null);

const clientCodeContent = "# Code to create Giskard client here";
const datasetCodeContent = "# Code to upload dataset here";
const modelCodeContent = "# Code to upload model here";
const scanCodeContent = "# Code to upload scan here";
const manualTestCodeContent = "# Code to upload manual test here";

const emit = defineEmits(["close"]);

const close = () => {
  emit("close");
  step.value = 1;
}

onMounted(async () => {
  try {
    allMLWorkerSettings.value = await api.getMLWorkerSettings();
    externalWorker.value = allMLWorkerSettings.value.find(worker => worker.isRemote === true) || null;
  } catch (error) { }

  if (externalWorker.value) {
    step.value = 2;
  }
})


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
        <div class="mb-6">
          Is your External ML worker running? {{ externalWorker !== null }}
        </div>
        <v-btn color="primary" @click="step = 2">Continue</v-btn>
        <v-btn class="ml-2" @click="close" flat>Cancel</v-btn>
      </v-stepper-content>

      <v-stepper-content step="2">
        <div class="mb-6">
          <p class="mb-2">Create a Giskard client with the following Python code:</p>
          <CodeSnippet :codeContent="clientCodeContent"></CodeSnippet>
        </div>
        <v-btn color="primary" @click="step = 3">Continue</v-btn>
        <v-btn class="ml-2" @click="close" flat>Cancel</v-btn>
      </v-stepper-content>

      <v-stepper-content step="3">
        <div class="mb-6">
          <p class="mb-2">Choose the type of artifact you want to create:</p>
          <v-btn-toggle v-model="toggleArtifactType" borderless mandatory color="primary">
            <v-btn value="dataset" class="py-5 px-4">
              <span>Dataset</span>
            </v-btn>
            <v-btn value="model" class="py-5 px-4">
              <span>Model</span>
            </v-btn>
          </v-btn-toggle>
          <p class="mt-4 mb-2">Then, create the artifact with the following Python code:</p>
          <CodeSnippet v-show="toggleArtifactType === 'dataset'" :codeContent="datasetCodeContent"></CodeSnippet>
          <CodeSnippet v-show="toggleArtifactType === 'model'" :codeContent="modelCodeContent"></CodeSnippet>
        </div>
        <v-btn color="primary" @click="step = 4">Continue</v-btn>
        <v-btn class="ml-2" @click="close" flat>Cancel</v-btn>
      </v-stepper-content>

      <v-stepper-content step="4">
        <div class="mb-6">
          <p class="mb-2">Choose the type of test you want to upload:</p>
          <v-btn-toggle v-model="toggleTestType" borderless mandatory color="primary">
            <v-btn value="scan" class="py-5 px-4">
              <span>Scan</span>
            </v-btn>
            <v-btn value="manual" class="py-5 px-4">
              <span>Manual</span>
            </v-btn>
          </v-btn-toggle>
          <p class="mt-4 mb-2">Then, upload the test with the following Python code:</p>
          <CodeSnippet v-show="toggleTestType === 'scan'" :codeContent="scanCodeContent"></CodeSnippet>
          <CodeSnippet v-show="toggleTestType === 'manual'" :codeContent="manualTestCodeContent"></CodeSnippet>
        </div>
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