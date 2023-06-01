<script setup lang="ts">
import { computed, ref } from "vue";

interface Props {
  isVisible: boolean
}

const props = defineProps<Props>();

const datasets = ref([
  {
    "id": 1,
    "name": "Dataset 1"
  },
  {
    "id": 2,
    "name": "Dataset 2"
  },
  {
    "id": 3,
    "name": "Dataset 3"
  }
]);

const models = ref([
  {
    "id": 1,
    "name": "Model 1"
  },
  {
    "id": 2,
    "name": "Model 2"
  },
  {
    "id": 3,
    "name": "Model 3"
  }
]);

const datasetsFormatted = computed(() => datasets.value.map(({name, id}) => appendIdToName(name, id)));
const modelsFormatted = computed(() => models.value.map(({name, id}) => appendIdToName(name, id)));

const inspectionName = ref("");
const datasetSelected = ref({});
const modelSelected = ref({});

const missingValues = computed(() => {
  return Object.keys(datasetSelected.value).length === 0 || Object.keys(modelSelected.value).length === 0;
});

const newInspection = computed(() => {
  return {
    "name": inspectionName.value,
    "createdDate": new Date(),
    "dataset": datasetSelected.value,
    "model": modelSelected.value
  }
});

const emit = defineEmits(['closeDialog', 'createInspection'])

function closeDialog() {
  inspectionName.value = "";
  datasetSelected.value = {};
  modelSelected.value = {};
  emit('closeDialog');
}

function createInspection() {
  emit('createInspection', newInspection.value);
}

function appendIdToName(name: string, id: number): string {
  if (name === "") {
    return id.toString();
  }
  return name + " (" + id + ")";
}
</script>

<template>
 <v-dialog v-model="isVisible" width="600">
    <v-card>
      <v-card-title class="headline">Create Inspection</v-card-title>
      <v-card-text>
        <v-text-field label="Inspection name (optional)" v-model="inspectionName"></v-text-field>
        <v-select label="Dataset" :items="datasetsFormatted" v-model="datasetSelected" required></v-select>
        <v-select label="Model" :items="modelsFormatted" v-model="modelSelected" required></v-select>
      </v-card-text>

      <v-card-actions>
        <v-btn text @click="closeDialog">Cancel</v-btn>
        <v-spacer></v-spacer>
        <v-btn color="primary" @click="createInspection" :disabled="missingValues">Create</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<style scoped>
</style>