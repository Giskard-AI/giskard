<script setup lang="ts">
import { api } from '@/api';
import { TYPE } from "vue-toastification";
import { DatasetDTO, ModelDTO } from "@/generated-sources";
import DatasetSelector from '@/views/main/utils/DatasetSelector.vue';
import ModelSelector from '@/views/main/utils/ModelSelector.vue';
import { computed, onActivated, ref } from "vue";
import { useMainStore } from "@/stores/main";
import { useDebuggingSessionsStore } from "@/stores/debugging-sessions";
import { useMLWorkerStore } from '@/stores/ml-worker';

const debuggingSessionsStore = useDebuggingSessionsStore();
const mlWorkerStore = useMLWorkerStore();

interface Props {
  projectId: number;
}

const props = defineProps<Props>();

const datasets = ref<DatasetDTO[]>([]);
const models = ref<ModelDTO[]>([]);
const currentStep = ref(1);
const loading = ref(false);

const dialog = ref(false);
const sessionName = ref("");
const selectedDataset = ref<DatasetDTO | null>(null);
const selectedModel = ref<ModelDTO | null>(null);

const missingValues = computed(() => {
  if (selectedDataset.value === null || selectedModel.value === null) {
    return true;
  }
  return false;
});

const emit = defineEmits(['createDebuggingSession'])

async function createNewDebuggingSession() {
  await mlWorkerStore.checkExternalWorkerConnection();

  if (!mlWorkerStore.isExternalWorkerConnected) {
    useMainStore().addNotification({
      content: 'ML Worker is not connected. Please start the ML Worker first and try again.',
      color: TYPE.ERROR,
    });
    throw new Error('ML Worker is not connected. Please start the ML Worker first and try again.');
  }

  loading.value = true;
  try {
    const newDebuggingSession = await debuggingSessionsStore.createDebuggingSession({
      datasetId: selectedDataset.value!.id,
      modelId: selectedModel.value!.id,
      name: sessionName.value,
      sample: false
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
  selectedDataset.value = null;
  selectedModel.value = null;
  sessionName.value = "";
  currentStep.value = 1;
}

async function loadDatasets() {
  datasets.value = await api.getProjectDatasets(props.projectId);
}

async function loadModels() {
  models.value = await api.getProjectModels(props.projectId);
}

onActivated(async () => {
  await loadDatasets();
  await loadModels();
});
</script>

<template>
  <div class="text-center">
    <v-dialog v-model="dialog" width="60vw">
      <template v-slot:activator="{ on, attrs }">
        <v-btn color="primaryLight" class="primaryLightBtn" v-bind="attrs" v-on="on" @click="resetInputs">
          <v-icon left>add</v-icon>
          New debugging session
        </v-btn>
      </template>
      <v-card>
        <v-card-title class="headline">Create a new debugging session</v-card-title>
        <v-card-text>
          <v-text-field label="Session name (optional)" v-model="sessionName" class="selector" outlined dense hide-details></v-text-field>
          <ModelSelector :projectId="projectId" :value.sync="selectedModel" class="selector"></ModelSelector>
          <v-spacer></v-spacer>
          <DatasetSelector :projectId="projectId" :value.sync="selectedDataset" :return-object="true" label="Dataset" class="selector"></DatasetSelector>
        </v-card-text>
        <v-card-actions>
          <v-btn text @click="closeDialog">Cancel</v-btn>
          <v-spacer></v-spacer>
          <v-btn color="primaryLight" class="primaryLightBtn" @click="createNewDebuggingSession" :disabled="missingValues" :loading="loading">Create</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<style scoped>
.selector {
  margin-top: 1rem;
  margin-bottom: 1.5rem;
}
</style>
