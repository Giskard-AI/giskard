<template>
  <div class="text-center">
    <v-dialog v-model="dialog" width="60vw">
      <template v-slot:activator="{ on, attrs }">
        <v-btn color="primaryLight" class="primaryLightBtn" v-bind="attrs" v-on="on" @click="resetInputs">
          <v-icon left>add</v-icon>
          New debugging session
        </v-btn>
      </template>
      <v-card v-if="isMLWorkerConnected">
        <v-card-title class="headline">Create a new debugging session</v-card-title>
        <v-card-text>
          <v-text-field label="Session name (optional)" v-model="sessionName" class="selector" outlined dense hide-details></v-text-field>
          <ModelSelector :projectId="projectId" :value.sync="selectedModelId" :return-object="false" label="Model" class="selector"></ModelSelector>
          <v-spacer></v-spacer>
          <DatasetSelector :projectId="projectId" :value.sync="selectedDatasetId" :return-object="false" label="Dataset" class="selector"></DatasetSelector>
        </v-card-text>
        <v-card-actions>
          <v-btn text @click="closeDialog">Cancel</v-btn>
          <v-spacer></v-spacer>
          <v-btn color="primaryLight" class="primaryLightBtn" @click="createNewDebuggingSession" :disabled="missingValues" :loading="loading">Create</v-btn>
        </v-card-actions>
      </v-card>
      <v-card v-else>
        <v-card-title class="py-6">
          <h2>ML Worker is not connected</h2>
        </v-card-title>
        <v-card-text>
          <StartWorkerInstructions></StartWorkerInstructions>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { TYPE } from "vue-toastification";
import DatasetSelector from '@/views/main/utils/DatasetSelector.vue';
import ModelSelector from '@/views/main/utils/ModelSelector.vue';
import { computed, ref } from "vue";
import { useMainStore } from "@/stores/main";
import { useDebuggingSessionsStore } from "@/stores/debugging-sessions";
import { state } from "@/socket";
import StartWorkerInstructions from "@/components/StartWorkerInstructions.vue";

const debuggingSessionsStore = useDebuggingSessionsStore();

interface Props {
  projectId: number;
}

const props = defineProps<Props>();

const currentStep = ref(1);
const loading = ref(false);
const dialog = ref(false);
const sessionName = ref("");
const selectedDatasetId = ref<string | null>();
const selectedModelId = ref<string | null>();

const isMLWorkerConnected = computed(() => {
  return state.workerStatus.connected;
});

const missingValues = computed(() => {
  if (selectedDatasetId.value === null || selectedModelId.value === null) {
    return true;
  }
  return false;
});

const emit = defineEmits(['createDebuggingSession'])

async function createNewDebuggingSession() {
  if (!isMLWorkerConnected.value) {
    useMainStore().addNotification({
      content: 'ML Worker is not connected. Please start the ML Worker first and try again.',
      color: TYPE.ERROR,
    });
    throw new Error('ML Worker is not connected. Please start the ML Worker first and try again.');
  }

  loading.value = true;
  try {
    const newDebuggingSession = await debuggingSessionsStore.createDebuggingSession({
      datasetId: selectedDatasetId.value!,
      modelId: selectedModelId.value!,
      name: sessionName.value,
      sample: true
    });
    debuggingSessionsStore.setCurrentDebuggingSessionId(newDebuggingSession.id);
    emit('createDebuggingSession', newDebuggingSession);
  } finally {
    loading.value = false;
    closeDialog();
  }
}

function closeDialog() {
  resetInputs();
  dialog.value = false;
}

function resetInputs() {
  selectedDatasetId.value = null;
  selectedModelId.value = null;
  sessionName.value = "";
  currentStep.value = 1;
}
</script>

<style scoped>
.selector {
  margin-top: 1rem;
  margin-bottom: 1.5rem;
}
</style>
