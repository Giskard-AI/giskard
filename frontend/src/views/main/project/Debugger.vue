<script setup lang="ts">
import { api } from '@/api';
import { InspectionDTO } from "@/generated-sources";
import InspectionDialog from "@/components/InspectionDialog.vue";
import { computed, ref, onActivated } from "vue";



interface Props {
  projectId: number;
}

const props = defineProps<Props>();

const inspections = ref<InspectionDTO[]>([]);

const activeInspection = ref<number | null>(null);
const searchInspection = ref("");
const showInspectionDialog = ref(false);

const displayComponents = computed(() => activeInspection.value == null);

async function loadInspections() {
  inspections.value = await api.getProjectInspections(props.projectId)
}

function toggleActiveInspection(id: number) {
  if (activeInspection.value === id) {
    activeInspection.value = null;
  } else {
    activeInspection.value = id;
  }
}

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

function formatDate(date: Date): string {
  return date.getFullYear() +
    "-" + (date.getMonth() + 1).toString().padStart(2, "0") +
    "-" + date.getDate().toString().padStart(2, "0") +
    " " + date.getHours().toString().padStart(2, "0") +
    ":" + date.getMinutes().toString().padStart(2, "0");
}

onActivated(() => loadInspections());
</script>

<template>
  <div class="vertical-container">
    <InspectionDialog :is-visible="showInspectionDialog" @closeDialog="closeInspectionDialog" @createInspection="(newInspection) => { logInspection(newInspection) }"></InspectionDialog>
    <v-container fluid class="vc" v-if="inspections.length > 0">
      <v-row v-show="displayComponents">
        <v-col cols="4">
          <v-text-field label="Search for an inspection session" append-icon="search" outlined v-model="searchInspection"></v-text-field>
        </v-col>
        <v-col cols="8">
          <div class="d-flex flex-row-reverse pb-4">
            <v-btn color="primary" @click="openInspectionDialog"><v-icon>add</v-icon> New Inspection</v-btn>
          </div>
        </v-col>
      </v-row>

      <v-expansion-panels>
        <v-row dense no-gutters class="mr-12 ml-6 caption secondary--text text--lighten-3 pb-2">
          <v-col cols="3">Name</v-col>
          <v-col cols="2">Id</v-col>
          <v-col cols="2">Created at</v-col>
          <v-col cols="1">Dataset name</v-col>
          <v-col cols="1">Dataset ID</v-col>
          <v-col cols="1">Model name</v-col>
          <v-col cols="1">Model ID</v-col>
          <v-col cols="1">Actions</v-col>
        </v-row>

        <v-expansion-panel v-for="inspection in inspections" :key="inspection.id" v-show="displayComponents || activeInspection == inspection.id" @click="toggleActiveInspection(inspection.id)">
          <v-expansion-panel-header>
            <v-row dense no-gutters class="align-center">
              <v-col cols="3">Generic name</v-col>
              <v-col cols="2">{{ inspection.id }}</v-col>
              <v-col cols="2">Generic date</v-col>
              <v-col cols="1">{{ inspection.dataset.name }}</v-col>
              <v-col cols="1">{{ inspection.dataset.id }}</v-col>
              <v-col cols="1">{{ inspection.model.name }}</v-col>
              <v-col cols="1">{{ inspection.model.id }}</v-col>
              <v-col cols="1">
                <v-card-actions>
                  <v-btn icon color="accent" class="delete-button" @click="deleteInspection(inspection.id)">
                    <v-icon>mdi-delete</v-icon>
                  </v-btn>
                </v-card-actions>
              </v-col>
            </v-row>
          </v-expansion-panel-header>
          <v-expansion-panel-content>
            <v-divider></v-divider>
            <p>Lorem ipsum dolor sit amet consectetur adipisicing elit. Earum commodi, maxime molestias temporibus autem harum dignissimos, voluptate animi soluta eos fugiat molestiae rerum et cum, laudantium in ab quisquam? Aperiam possimus, quam quos beatae sit maiores minima asperiores recusandae deleniti, molestiae dignissimos architecto, nobis tenetur dolor quidem ad in incidunt rerum obcaecati velit. Sed, nemo. Vitae, dolorem quia! Libero dolorem ex esse quaerat quas consequuntur voluptates blanditiis perspiciatis doloribus. Doloribus, sit ad consequuntur cumque doloremque, optio ratione veniam et, quas temporibus fuga facilis.</p>
          </v-expansion-panel-content>
        </v-expansion-panel>
      </v-expansion-panels>
    </v-container>

    <v-container v-else class="vc mt-12">
      <v-alert class="text-center">
        <h1 class="headline bold">No debugging sessions found</h1>
        <p class="create-inspection-message">You haven't created any debugging session for this project. Please, create a new one in order to use this functionality.</p>
        <v-btn tile class='mx-1' @click="openInspectionDialog" color="primary">
          <v-icon>add</v-icon>
          Create a new debugging session
        </v-btn>
      </v-alert>
      <div class="d-flex justify-center mb-6">
        <img src="@/assets/logo_debugger.png" title="Debugger tab logo" alt="A turtle using a magnifying glass" width="30%">
      </div>
    </v-container>
  </div>
</template>

<style scoped>
.create-inspection-message {
  margin-bottom: 1.5rem;
  font-size: 1.125rem;
}
</style>