<script setup lang="ts">
import { ref } from "vue";
import InspectionDialog from "@/components/InspectionDialog.vue";

const inspections = ref([
  {
    "id": 1,
    "name": "Inspection 1",
    "createdDate": new Date("2023-04-17T12:00:00.000Z"),
    "dataset": {
      "id": 1,
      "name": "Dataset 1"
    },
    "model": {
      "id": 1,
      "name": "Model 1"
    }
  },
  {
    "id": 2,
    "name": "Inspection 2",
    "createdDate": new Date("2023-04-17T12:00:00.000Z"),
    "dataset": {
      "id": 2,
      "name": "Dataset 2"
    },
    "model": {
      "id": 2,
      "name": "Model 2"
    }
  },
  {
    "id": 3,
    "name": "Inspection 3",
    "createdDate": new Date("2023-04-17T12:00:00.000Z"),
    "dataset": {
      "id": 3,
      "name": "Dataset 3"
    },
    "model": {
      "id": 3,
      "name": "Model 3"
    }
  }
]);

const searchInspection = ref("");
const showInspectionDialog = ref(false);

function openInspectionDialog() {
  closeInspectionDialog();
  showInspectionDialog.value = true;

}

function closeInspectionDialog() {
  showInspectionDialog.value = false;
}

function openInspection(id: number) {
  console.log("Open inspection " + id);
}

function logInspection(inspection: any) {
  console.log(inspection);
}

function deleteInspection(id: number) {
  console.log("Delete inspection " + id);
}

function formatDate(date: Date) : string {
  return date.getFullYear() + 
         "-" + (date.getMonth() + 1).toString().padStart(2, "0") + 
         "-" + date.getDate().toString().padStart(2, "0") + 
         " " + date.getHours().toString().padStart(2, "0") + 
         ":" + date.getMinutes().toString().padStart(2, "0");
}
</script>

<template>
  <div>
  <InspectionDialog :is-visible="showInspectionDialog" @closeDialog="closeInspectionDialog"
  @createInspection="(newInspection) => {logInspection(newInspection)}"></InspectionDialog>
  <v-container fluid class="vc" v-if="inspections.length > 0">
    <v-row>
      <v-col cols="4">
        <v-text-field label="Search for an inspection session" append-icon="search" outlined v-model="searchInspection"></v-text-field>
      </v-col>
      <v-col cols="8">
        <div class="d-flex flex-row-reverse pb-4">
          <v-btn color="primary" @click="openInspectionDialog"><v-icon>add</v-icon> New Inspection</v-btn>
        </div>
      </v-col>
    </v-row>

    <v-card flat>
      <v-row class="px-2 py-1 caption secondary--text text--lighten-3">
        <v-col cols="2">Name</v-col>
        <v-col cols="1">Id</v-col>
        <v-col cols="2">Created at</v-col>
        <v-col cols="1">Dataset name</v-col>
        <v-col cols="1">Dataset ID</v-col>
        <v-col cols="1">Model name</v-col>
        <v-col cols="1">Model ID</v-col>
        <v-col cols="2">Actions</v-col>
      </v-row>
    </v-card>

    <v-card outlined tile class="grey lighten-5" v-for="inspection in inspections" :key="inspection.id">
      <v-row class="px-2 py-1 align-center">
        <v-col cols="2">{{ inspection.name }}</v-col>
        <v-col cols="1">{{ inspection.id }}</v-col>
        <v-col cols="2">{{ formatDate(inspection.createdDate) }}</v-col>
        <v-col cols="1">{{ inspection.dataset.name }}</v-col>
        <v-col cols="1">{{ inspection.dataset.id }}</v-col>
        <v-col cols="1">{{ inspection.model.name }}</v-col>
        <v-col cols="1">{{ inspection.model.id }}</v-col>
        <v-col cols="2">
          <v-btn 
            small tile color="primary"
            @click="openInspection(inspection.id)">
            <v-icon dense left>policy</v-icon>
            Open
          </v-btn>
          <v-btn 
            icon color="accent"
            class="delete-button"
            @click="deleteInspection(inspection.id)">
            <v-icon>mdi-delete</v-icon>
          </v-btn>
        </v-col>
      </v-row>
      <v-divider></v-divider>
    </v-card>
  </v-container>

  <v-container v-else class="d-flex flex-column vc fill-height">
    <h1 class="pt-16 create-inspection-message">You haven't created any inspection session for this project!</h1>
    <v-btn tile class='mx-1'
           @click="openInspectionDialog"
           color="primary">
      <v-icon>add</v-icon>
      Create a new inspection
    </v-btn>
  </v-container>  
</div>
</template>

<style scoped>
.delete-button {
  margin-left: 0.5rem;
}

.create-inspection-message {
  margin-bottom: 0.5rem;
}
</style>