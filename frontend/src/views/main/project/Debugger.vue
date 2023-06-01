<script setup lang="ts">
import { api } from '@/api';
import { InspectionDTO } from "@/generated-sources";
import InspectionDialog from "@/components/InspectionDialog.vue";
import InspectorWrapper from './InspectorWrapper.vue';
import { computed, ref, onActivated } from "vue";

interface Props {
  projectId: number;
  activeInspectionId: number | null;
}

const props = withDefaults(defineProps<Props>(), {
  activeInspectionId: null
});

const inspections = ref<InspectionDTO[]>([]);
const searchInspection = ref("");

const displayComponents = computed(() => props.activeInspectionId === null);

const filteredInspections = computed(() => {
  if (searchInspection.value.length == 0) return inspections.value;

  return inspections.value.filter((inspection) => {
    const dataset = inspection.dataset;
    const model = inspection.model;

    const search = searchInspection.value.toLowerCase();
    return (
      inspection.id.toString().includes(search) ||
      inspection.name.toLowerCase().includes(search) ||
      dataset.name.toLowerCase().includes(search) ||
      dataset.id.toString().includes(search) ||
      model.name.toLowerCase().includes(search) ||
      model.id.toString().includes(search)
    );
  });

})

async function loadInspections() {
  inspections.value = await api.getProjectInspections(props.projectId)
}


function toggleActiveInspection(newActiveInspectionId: Props["activeInspectionId"]) {
  if (props.activeInspectionId === newActiveInspectionId) {
    props.activeInspectionId = null;
  } else {
    props.activeInspectionId = newActiveInspectionId;
  }
}

function createNewInspection(newInspection: InspectionDTO) {
  inspections.value.push(newInspection);
  toggleActiveInspection(null);
  setTimeout(() => {
    toggleActiveInspection(newInspection.id);
  });
}

async function deleteInspection(id: number) {
  await api.deleteInspection(id);
  await loadInspections();

}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);

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
    <v-container fluid class="vc" v-if="inspections.length > 0">
      <v-row>
        <v-col cols="4">
          <v-text-field v-show="displayComponents" label="Search for an inspection session" append-icon="search" outlined v-model="searchInspection"></v-text-field>
        </v-col>
        <v-col cols="8">
          <div class="d-flex justify-end">
            <v-btn v-if="!displayComponents" @click="toggleActiveInspection(null)" class="mr-4 pa-2">
              <v-icon>mdi-arrow-u-left-top</v-icon> Show past inspections
            </v-btn>
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

        <v-expansion-panel v-for="inspection in filteredInspections" :key="inspection.id" v-show="displayComponents" @click="toggleActiveInspection(inspection.id)">
          <v-expansion-panel-header :disableIconRotate="true">
            <v-row dense no-gutters class="align-center">
              <v-col cols="3">{{ inspection.name }}</v-col>
              <v-col cols="1">{{ inspection.id }}</v-col>
              <v-col cols="2">{{ formatDate(inspection.createdDate) }}</v-col>
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
          </v-expansion-panel-header>
        </v-expansion-panel>
      </v-expansion-panels>
      <InspectorWrapper v-if="!displayComponents" :projectId="projectId" :inspectionId="activeInspectionId"></InspectorWrapper>
    </v-container>

    <v-container v-else class="vc mt-12">
      <v-alert class="text-center">
        <p class="create-inspection-message headline blue-grey--text">You haven't created any inspection session for this project. <br>Please create your first inspection session to start debugging your model.</p>
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