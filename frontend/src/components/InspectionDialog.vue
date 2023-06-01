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
const currentStep = ref(1);

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

const emit = defineEmits(['createInspection'])

async function createNewInspection() {
  const inspection = await api.prepareInspection({
    datasetId: selectedDataset.value!.id,
    modelId: selectedModel.value!.id
  });

  closeDialog();

  emit('createInspection', inspection);
}

function closeDialog() {
  resetInputs();
  dialog.value = false;
}

function resetInputs() {
  selectedDataset.value = null;
  selectedModel.value = null;
  inspectionName.value = "";
  currentStep.value = 1;
}

async function loadDatasets() {
  datasets.value = await api.getProjectDatasets(props.projectId);
}

async function loadModels() {
  models.value = await api.getProjectModels(props.projectId);
}

onActivated(() => {
  loadDatasets();
  loadModels();
});
</script>

<template>
  <div class="text-center">
    <v-dialog v-model="dialog" width="60vw">
      <template v-slot:activator="{ on, attrs }">
        <v-btn color="primary" v-bind="attrs" v-on="on" @click="resetInputs">
          <v-icon>add</v-icon>
          New Inspection Session
        </v-btn>
      </template>
      <v-stepper non-linear v-model="currentStep">
        <v-stepper-header>
          <v-stepper-step step="1" :complete="currentStep > 1">
            Select a model
          </v-stepper-step>
          <v-divider></v-divider>
          <v-stepper-step step="2" :complete="currentStep > 2">
            Select a dataset
          </v-stepper-step>
          <v-divider></v-divider>
          <v-stepper-step step="3" :complete="currentStep > 3">
            Define a inspection name
            <small>Optional</small>
          </v-stepper-step>
          <v-divider></v-divider>
          <v-stepper-step step="4" :complete="currentStep > 4">
            Review
          </v-stepper-step>
        </v-stepper-header>

        <v-stepper-items>
          <v-stepper-content step="1">
            <v-card>
              <v-card-text>
                <ModelSelector :projectId="projectId" :value.sync="selectedModel" class="selector"></ModelSelector>
              </v-card-text>
              <v-card-actions>
                <v-btn text @click="closeDialog">Cancel</v-btn>
                <v-spacer></v-spacer>
                <v-btn color="primary" @click="currentStep = 2" :disabled="selectedModel === null">Next</v-btn>
              </v-card-actions>
            </v-card>
          </v-stepper-content>

          <v-stepper-content step="2">
            <v-card>
              <v-card-text>
                <DatasetSelector :projectId="projectId" :value.sync="selectedDataset" :label="'Dataset'" class="selector"></DatasetSelector>
              </v-card-text>
              <v-card-actions class="d-flex justify-space-between">
                <v-btn text @click="closeDialog">Cancel</v-btn>
                <div class="d-flex justify-end">
                  <v-btn text @click="currentStep = 1" class="mr-2">Back</v-btn>
                  <v-btn color="primary" @click="currentStep = 3" :disabled="selectedDataset === null">Next</v-btn>
                </div>
              </v-card-actions>
            </v-card>
          </v-stepper-content>

          <v-stepper-content step="3">
            <v-card>
              <v-card-text>
                <v-text-field label="Inspection name (optional)" class="selector" v-model="inspectionName" outlined dense hide-details></v-text-field>
              </v-card-text>
              <v-card-actions class="d-flex justify-space-between">
                <v-btn text @click="closeDialog">Cancel</v-btn>
                <div class="d-flex justify-end">
                  <v-btn text @click="currentStep = 2" class="mr-2">Back</v-btn>
                  <v-btn color="primary" @click="currentStep = 4">Next</v-btn>
                </div>
              </v-card-actions>
            </v-card>
          </v-stepper-content>

          <v-stepper-content step="4">
            <v-card>
              <v-card-text>
                <v-list class="d-flex">
                  <v-list-item>
                    <v-list-item-content>
                      <v-list-item-title>Model</v-list-item-title>
                      <v-list-item-subtitle>{{ selectedModel?.name }}</v-list-item-subtitle>
                    </v-list-item-content>
                  </v-list-item>
                  <v-list-item>
                    <v-list-item-content>
                      <v-list-item-title>Dataset</v-list-item-title>
                      <v-list-item-subtitle>{{ selectedDataset?.name }}</v-list-item-subtitle>
                    </v-list-item-content>
                  </v-list-item>
                  <v-list-item>
                    <v-list-item-content>
                      <v-list-item-title>Inspection name</v-list-item-title>
                      <v-list-item-subtitle>{{ inspectionName || '-' }}</v-list-item-subtitle>
                    </v-list-item-content>
                  </v-list-item>
                </v-list>
              </v-card-text>
              <v-card-actions class="d-flex justify-space-between">
                <v-btn text @click="closeDialog">Cancel</v-btn>
                <div class="d-flex justify-end">
                  <v-btn text @click="currentStep = 3" class="mr-2">Back</v-btn>
                  <v-btn color="primary" @click="createNewInspection" :disabled="missingValues">Create</v-btn>
                </div>
              </v-card-actions>
            </v-card>
          </v-stepper-content>
        </v-stepper-items>
      </v-stepper>
    </v-dialog>
  </div>
</template>

<style scoped>
.selector {
  margin-top: 1rem;
  margin-bottom: 1.5rem;
}
</style>