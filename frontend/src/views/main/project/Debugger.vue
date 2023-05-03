<script setup lang="ts">
import { computed, ref, onActivated, watch } from "vue";
import { $vfm } from 'vue-final-modal';
import { api } from '@/api';
import { useRoute, useRouter } from 'vue-router/composables';
import { InspectionDTO } from "@/generated-sources";
import AddDebuggingSessionModal from '@/components/AddDebuggingSessionModal.vue';
import InlineEditText from '@/components/InlineEditText.vue';
import ConfirmModal from './modals/ConfirmModal.vue';

const route = useRoute();
const router = useRouter();

interface Props {
  projectId: number;
}

const props = defineProps<Props>();
const activeDebuggingSessionId = ref<number | null>(null);
const debuggingSessions = ref<InspectionDTO[]>([]);
const searchSession = ref("");
const openInspectionWrapper = ref(false);

const filteredSessions = computed(() => {

  return orderByDate(debuggingSessions.value.filter((session) => {
    const dataset = session.dataset;
    const model = session.model;

    const search = searchSession.value.toLowerCase();
    return (
      session.id.toString().includes(search) ||
      session.name.toLowerCase().includes(search) ||
      dataset.name.toLowerCase().includes(search) ||
      dataset.id.toString().includes(search) ||
      model.name.toLowerCase().includes(search) ||
      model.id.toString().includes(search)
    );
  }));

})

async function fetchDebuggingSessions() {
  debuggingSessions.value = await api.getProjectInspections(props.projectId)
}

async function showPastSessions() {
  resetSearchInput();
  activeDebuggingSessionId.value = null;
  openInspectionWrapper.value = false;
  await router.push({
    name: 'project-debugger',
    params: {
      projectId: props.projectId.toString()
    }
  });
}

async function createDebuggingSession(debuggingSession: InspectionDTO) {
  await fetchDebuggingSessions();
  activeDebuggingSessionId.value = debuggingSession.id;
  openInspectionWrapper.value = true;
  await openInspection(props.projectId.toString(), debuggingSession.id.toString());
}

async function renameSession(id: number, name: string) {
  const currentSession = debuggingSessions.value.find(s => s.id === id);
  if (currentSession) {
    currentSession.name = name;
    await api.updateInspectionName(id, {
      name: name,
      datasetId: currentSession.dataset.id,
      modelId: currentSession.model.id
    });
  }
}

function orderByDate(debuggingSessions: InspectionDTO[]): InspectionDTO[] {
  return debuggingSessions.sort((a, b) => {
    const aDate = new Date(a.createdDate);
    const bDate = new Date(b.createdDate);

    return bDate.getTime() - aDate.getTime();
  });
}

function deleteDebuggingSession(debuggingSession: InspectionDTO) {
  $vfm.show({
    component: ConfirmModal,
    bind: {
      title: 'Delete debugging session',
      text: `Are you sure that you want to delete the debugging session '${debuggingSession.name}'?`,
      isWarning: true
    },
    on: {
      async confirm(close) {
        await api.deleteInspection(debuggingSession.id);
        await fetchDebuggingSessions();
        close();
      }
    }
  });
}

async function openDebuggingSession(debuggingSessionId: number, projectId: number) {
  activeDebuggingSessionId.value = debuggingSessionId;
  openInspectionWrapper.value = true;
  await openInspection(projectId.toString(), debuggingSessionId.toString());
}

function resetSearchInput() {
  searchSession.value = "";
}

async function openInspection(projectId: string, inspectionId: string) {
  await router.push({
    name: 'inspection',
    params: {
      projectId,
      inspectionId
    }
  });
}

function handleRouteChanged() {
  openInspectionWrapper.value = route.meta && route.meta.openInspectionWrapper
}

watch(() => route.meta, () => handleRouteChanged());

onActivated(async () => {
  if (activeDebuggingSessionId.value) {
    await openInspection(props.projectId.toString(), activeDebuggingSessionId.value.toString());
  }
  fetchDebuggingSessions();
  handleRouteChanged();
});

</script>

<template>
  <div class="vertical-container">
    <v-container fluid class="vc" v-if="debuggingSessions.length > 0">
      <v-row>
        <v-col cols="4">
          <v-text-field v-show="!openInspectionWrapper" label="Search for a debugging session" append-icon="search" outlined v-model="searchSession"></v-text-field>
        </v-col>
        <v-col cols="8">
          <div class="d-flex justify-end">
            <v-btn v-if="openInspectionWrapper" @click="showPastSessions" class="mr-4 pa-2 text--secondary">
              <v-icon left>history</v-icon>Past sessions
            </v-btn>
            <AddDebuggingSessionModal v-bind:project-id="projectId" v-on:createDebuggingSession="createDebuggingSession"></AddDebuggingSessionModal>
          </div>
        </v-col>
      </v-row>

      <v-expansion-panels>
        <v-row class="mr-12 ml-6 caption secondary--text text--lighten-3 pb-2" v-if="!openInspectionWrapper">
          <v-col cols="3">Session name</v-col>
          <v-col cols="1">Session ID</v-col>
          <v-col cols="2">Created at</v-col>
          <v-col cols="1">Dataset name</v-col>
          <v-col cols="1">Dataset ID</v-col>
          <v-col cols="2">Model name</v-col>
          <v-col cols="1">Model ID</v-col>
          <v-col cols="1"></v-col>
        </v-row>

        <v-expansion-panel v-for="session in filteredSessions" :key="session.id" v-show="!openInspectionWrapper" @click.stop="openDebuggingSession(session.id, projectId)" class="expansion-panel">
          <v-expansion-panel-header :disableIconRotate="true" class="grey lighten-5" tile>
            <v-row class="px-2 py-1 align-center">
              <v-col cols="3">
                <InlineEditText :text="session.name" @save="(name) => renameSession(session.id, name)">
                </InlineEditText>
              </v-col>
              <v-col cols="1">{{ session.id }}</v-col>
              <v-col cols="2">{{ session.createdDate | date }}</v-col>
              <v-col cols="1">{{ session.dataset.name }}</v-col>
              <v-col cols="1" class="id-container" :title="session.dataset.id">{{ session.dataset.id }}</v-col>
              <v-col cols="2">{{ session.model.name }}</v-col>
              <v-col cols="1" class="id-container" :title="session.dataset.id">{{ session.model.id }}</v-col>
              <v-col cols="1">
                <v-card-actions>
                  <v-btn icon @click.stop="deleteDebuggingSession(session)" @click.stop.prevent>
                    <v-icon color="accent">delete</v-icon>
                  </v-btn>
                </v-card-actions>
              </v-col>
            </v-row>
          </v-expansion-panel-header>
        </v-expansion-panel>
      </v-expansion-panels>
      <div v-if="openInspectionWrapper">
        <router-view />
      </div>
    </v-container>

    <v-container v-else class="vc mt-6">
      <v-alert class="text-center">
        <p class="headline font-weight-medium grey--text text--darken-2">You haven't created any debugging session for this project. <br>Please create your first session to start debugging your model.</p>
      </v-alert>
      <AddDebuggingSessionModal v-bind:project-id="projectId" v-on:createDebuggingSession="createDebuggingSession"></AddDebuggingSessionModal>
      <div class="d-flex justify-center mb-6">
        <img src="@/assets/logo_debugger.png" class="debugger-logo" title="Debugger tab logo" alt="A turtle using a magnifying glass">
      </div>
    </v-container>
  </div>
</template>

<style scoped>
.debugger-logo {
  width: max(20vw, 150px);
  margin-top: 2rem;
}

.id-container {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding: 0.5rem;
}

.expansion-panel {
  margin-top: 10px !important;
}
</style>