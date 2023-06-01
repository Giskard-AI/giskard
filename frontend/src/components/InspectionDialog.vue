<script setup lang="ts">
import { api } from '@/api';
import { DatasetDTO, ModelDTO } from "@/generated-sources";
import DatasetSelector from '@/views/main/utils/DatasetSelector.vue';
import ModelSelector from '@/views/main/utils/ModelSelector.vue';
import { computed, onActivated, ref } from "vue";

interface Props {
  projectId: number;
}

const props = defineProps<Props>();

const datasets = ref<DatasetDTO[]>([]);
const models = ref<ModelDTO[]>([]);

const dialog = ref(false);
const inspectionName = ref("");
const selectedDataset = ref<DatasetDTO | null>(null);
const selectedModel = ref<ModelDTO | null>(null);

const missingValues = computed(() => {
  if (selectedDataset.value === null || selectedModel.value === null) {
    return true;
  }
  return false;
});

const newInspection = computed(() => {
  return {
    "name": inspectionName.value,
    "createdDate": new Date(),
    "dataset": selectedDataset.value,
    "model": selectedModel.value
  }
});

const emit = defineEmits(['createInspection'])

async function loadDatasets() {
  datasets.value = await api.getProjectDatasets(props.projectId);
}

async function loadModels() {
  models.value = await api.getProjectModels(props.projectId);
}

function createInspection() {
  emit('createInspection', newInspection.value);
}

onActivated(() => {
  loadDatasets();
  loadModels();
});
</script>

<template>
  <div class="text-center">
    <v-dialog v-model="dialog" width="80vw">
      <template v-slot:activator="{ on, attrs }">
        <v-btn color="primary" v-bind="attrs" v-on="on">
          <v-icon>add</v-icon>
          New Debugging Session
        </v-btn>
      </template>
      <v-card>
        <v-card-title class="headline">Create Inspection</v-card-title>
        <v-card-text>
          <v-text-field label="Inspection name (optional)" v-model="inspectionName" outlined dense hide-details></v-text-field>
          <ModelSelector :projectId="projectId" :value.sync="selectedModel" class="selector"></ModelSelector>
          <v-spacer></v-spacer>
          <DatasetSelector :projectId="projectId" :value.sync="selectedDataset" :label="'Dataset'" class="selector"></DatasetSelector>

        </v-card-text>
        <v-card-actions>
          <v-btn text @click="dialog = false">Cancel</v-btn>
          <v-spacer></v-spacer>
          <v-btn color="primary" @click="createInspection" :disabled="missingValues">Create</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<style scoped>
.selector {
  margin-top: 1.5rem;
}
</style>