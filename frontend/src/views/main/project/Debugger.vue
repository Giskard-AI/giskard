<script setup lang="ts">
import { api } from '@/api';
import { InspectionDTO } from "@/generated-sources";
import InspectionDialog from "@/components/InspectionDialog.vue";
import InspectorWrapper from './InspectorWrapper.vue';
import { computed, ref, onActivated } from "vue";

interface Props {
  projectId: number;
}

const props = defineProps<Props>();

const inspections = ref<InspectionDTO[]>([]);
const activeInspection = ref<number | null>(null);
const searchInspection = ref("");

const displayComponents = computed(() => activeInspection.value == null);

async function loadInspections() {
  inspections.value = await api.getProjectInspections(props.projectId)
  // inspections.value = [];
}

function toggleActiveInspection(id: number) {
  if (activeInspection.value === id) {
    activeInspection.value = null;
  } else {
    activeInspection.value = id;
  }
}

function createNewInspection(newInspection: InspectionDTO) {
  inspections.value.push(newInspection);
  // toggleActiveInspection(newInspection.id); // TODO: this is not working properly
}

async function deleteInspection(id: number) {
  await api.deleteInspection(id);
  await loadInspections();

}

// function formatDate(date: Date): string {
//   return date.getFullYear() +
//     "-" + (date.getMonth() + 1).toString().padStart(2, "0") +
//     "-" + date.getDate().toString().padStart(2, "0") +
//     " " + date.getHours().toString().padStart(2, "0") +
//     ":" + date.getMinutes().toString().padStart(2, "0");
// }

onActivated(() => loadInspections());
</script>

<template>
  <div class="vertical-container">
    <v-container fluid class="vc" v-if="inspections.length > 0">
      <v-row v-show="displayComponents">
        <v-col cols="4">
          <v-text-field label="Search for an inspection session" append-icon="search" outlined v-model="searchInspection"></v-text-field>
        </v-col>
        <v-col cols="8">
          <div class="d-flex flex-row-reverse pb-4">
            <InspectionDialog v-bind:project-id="projectId" v-on:createInspection="createNewInspection"></InspectionDialog>
          </div>
        </v-col>
      </v-row>

      <v-expansion-panels>
        <v-row dense no-gutters class="mr-12 ml-6 caption secondary--text text--lighten-3 pb-2" v-if="displayComponents">
          <v-col cols="3">Name</v-col>
          <v-col cols="1">ID</v-col>
          <v-col cols="2">Created at</v-col>
          <v-col cols="1">Dataset name</v-col>
          <v-col cols="1">Dataset ID</v-col>
          <v-col cols="2">Model name</v-col>
          <v-col cols="1">Model ID</v-col>
          <v-col cols="1">Actions</v-col>
        </v-row>

        <v-expansion-panel v-for="inspection in inspections" :key="inspection.id" v-show="displayComponents || activeInspection == inspection.id" @click="toggleActiveInspection(inspection.id)">
          <v-expansion-panel-header>
            <v-row dense no-gutters class="align-center" v-if="displayComponents">
              <v-col cols="3">Generic name</v-col>
              <v-col cols="1">{{ inspection.id }}</v-col>
              <v-col cols="2">Generic date</v-col>
              <v-col cols="1">{{ inspection.dataset.name }}</v-col>
              <v-col cols="1" class="id-container" :title="inspection.dataset.id">{{ inspection.dataset.id }}</v-col>
              <v-col cols="2">{{ inspection.model.name }}</v-col>
              <v-col cols="1" class="id-container" :title="inspection.dataset.id">{{ inspection.model.id }}</v-col>
              <v-col cols="1">
                <v-card-actions>
                  <v-btn icon color="accent" class="delete-button" @click.stop="deleteInspection(inspection.id)">
                    <v-icon>mdi-delete</v-icon>
                  </v-btn>
                </v-card-actions>
              </v-col>
            </v-row>
            <v-row dense no-gutters class="align-center" v-else>
              <v-tooltip bottom>
                <template v-slot:activator="{ on, attrs }">
                  <v-icon v-on="on" class="pr-5" medium>info</v-icon>
                </template>
                <h3> Inspection </h3>
                <div class="d-flex">
                  <div> Id</div>
                  <v-spacer />
                  <div> {{ inspection.id }}</div>
                </div>
                <div class="d-flex">
                  <div> Name</div>
                  <v-spacer />
                  <div class="pl-5"> Generic name </div>
                </div>
                <br />
                <h3> Model </h3>
                <div class="d-flex">
                  <div> Id</div>
                  <v-spacer />
                  <div> {{ inspection.model.id }}</div>
                </div>
                <div class="d-flex">
                  <div> Name</div>
                  <v-spacer />
                  <div class="pl-5"> {{ inspection.model.name }}</div>
                </div>
                <br />
                <h3> Dataset </h3>
                <div class="d-flex">
                  <div> Id</div>
                  <v-spacer />
                  <div> {{ inspection.dataset.id }}</div>
                </div>
                <div class="d-flex">
                  <div> Name</div>
                  <v-spacer />
                  <div class="pl-5"> {{ inspection.dataset.name }}</div>
                </div>
              </v-tooltip>
              <h1 class="headline">Inspection: Generic name (ID: {{ inspection.id }})</h1>
            </v-row>
          </v-expansion-panel-header>
          <v-expansion-panel-content>
            <v-divider></v-divider>
            <InspectorWrapper :projectId="projectId" :inspectionId="inspection.id" v-if="inspection.id === activeInspection"></InspectorWrapper>
          </v-expansion-panel-content>
        </v-expansion-panel>
      </v-expansion-panels>
    </v-container>

    <v-container v-else class="vc mt-12">
      <v-alert class="text-center">
        <h1 class="headline bold">No debugging sessions found</h1>
        <p class="create-inspection-message">You haven't created any debugging session for this project. Please, create a new one in order to use this functionality.</p>
      </v-alert>
      <InspectionDialog v-bind:project-id="projectId" v-on:createInspection="createNewInspection"></InspectionDialog>
      <div class="d-flex justify-center mb-6">
        <img src="@/assets/logo_debugger.png" class="debugger-logo" title="Debugger tab logo" alt="A turtle using a magnifying glass">
      </div>
    </v-container>
  </div>
</template>

<style scoped>
.create-inspection-message {
  font-size: 1.125rem;
}

.debugger-logo {
  max-width: 30%;
  margin-top: 2rem;
}

.id-container {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding: 0.5rem;
}
</style>