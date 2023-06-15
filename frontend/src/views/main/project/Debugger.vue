<script setup lang="ts">
import { computed, ref, onActivated } from "vue";
import { $vfm } from 'vue-final-modal';
import { api } from '@/api';
import { useRouter } from 'vue-router/composables';
import { useDebuggingSessionsStore } from "@/stores/debugging-sessions";
import { InspectionDTO } from "@/generated-sources";
import AddDebuggingSessionModal from '@/components/AddDebuggingSessionModal.vue';
import InlineEditText from '@/components/InlineEditText.vue';
import ConfirmModal from './modals/ConfirmModal.vue';
import StartWorkerInstructions from "@/components/StartWorkerInstructions.vue";
import { state } from "@/socket";

const router = useRouter();

const debuggingSessionsStore = useDebuggingSessionsStore();

interface Props {
  projectId: number;
}

const props = defineProps<Props>();

const searchSession = ref("");

const isMLWorkerConnected = computed(() => {
  return state.workerStatus.connected;
});

const filteredSessions = computed(() => {

  return orderByDate(debuggingSessionsStore.debuggingSessions.filter((session) => {
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


async function showPastSessions() {
  debuggingSessionsStore.reload();
  resetSearchInput();
  debuggingSessionsStore.setCurrentDebuggingSessionId(null);
  await router.push({
    name: 'project-debugger',
    params: {
      projectId: props.projectId.toString()
    }
  });
}

async function createDebuggingSession(debuggingSession: InspectionDTO) {
  debuggingSessionsStore.reload();
  debuggingSessionsStore.setCurrentDebuggingSessionId(debuggingSession.id);
  await openInspection(props.projectId.toString(), debuggingSession.id.toString());
}

async function renameSession(id: number, name: string) {
  const currentSession = debuggingSessionsStore.debuggingSessions.find(s => s.id === id);
  if (currentSession) {
    currentSession.name = name;
    debuggingSessionsStore.updateDebuggingSessionName(id, {
      name,
      datasetId: currentSession.dataset.id,
      modelId: currentSession.model.id,
      sample: currentSession.sample
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
        await debuggingSessionsStore.reload();
        close();
      }
    }
  });
}

async function openDebuggingSession(debuggingSessionId: number, projectId: number) {
  debuggingSessionsStore.setCurrentDebuggingSessionId(debuggingSessionId);
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

onActivated(async () => {
  if (debuggingSessionsStore.currentDebuggingSessionId !== null) {
    await openInspection(props.projectId.toString(), debuggingSessionsStore.currentDebuggingSessionId.toString());
  } else {
    await debuggingSessionsStore.loadDebuggingSessions(props.projectId);
  }
});

</script>

<template>
  <div v-if="isMLWorkerConnected" class="vertical-container">
    <v-container fluid class="vc" v-if="debuggingSessionsStore.debuggingSessions.length > 0">
      <v-row>
        <v-col cols="4">
          <v-text-field v-show="debuggingSessionsStore.currentDebuggingSessionId === null" label="Search for a debugging session" append-icon="search" outlined v-model="searchSession"></v-text-field>
        </v-col>
        <v-col cols="8">
          <div class="d-flex justify-end">
            <v-btn v-if="debuggingSessionsStore.currentDebuggingSessionId !== null" text @click="showPastSessions" class="mr-3">
              <v-icon class="mr-2">mdi-arrow-left</v-icon>
              Back to all sessions
            </v-btn>
            <AddDebuggingSessionModal v-show="debuggingSessionsStore.currentDebuggingSessionId === null" :projectId="projectId" @createDebuggingSession="createDebuggingSession"></AddDebuggingSessionModal>
          </div>
        </v-col>
      </v-row>

      <v-expansion-panels v-if="debuggingSessionsStore.currentDebuggingSessionId === null">
        <v-row class="mr-12 ml-6 caption secondary--text text--lighten-3 pb-2">
          <v-col cols="3" class="col-container" title="Session name">Session name</v-col>
          <v-col cols="1" class="col-container" title="Session ID">Session ID</v-col>
          <v-col cols="2" class="col-container" title="Created at">Created at</v-col>
          <v-col cols="1" class="col-container" title="Dataset name">Dataset name</v-col>
          <v-col cols="1" class="col-container" title="Dataset ID">Dataset ID</v-col>
          <v-col cols="2" class="col-container" title="Model name">Model name</v-col>
          <v-col cols="1" class="col-container" title="Model ID">Model ID</v-col>
          <v-col cols="1"></v-col>
        </v-row>

        <v-expansion-panel v-for="session in filteredSessions" :key="session.id" @click.stop="openDebuggingSession(session.id, projectId)" class="expansion-panel">
          <v-expansion-panel-header :disableIconRotate="true" class="grey lighten-5" tile>
            <v-row class="px-2 py-1 align-center">
              <v-col cols="3" class="font-weight-bold" :title="session.name">
                <div class="pr-4">
                  <InlineEditText :text="session.name" @save="(name) => renameSession(session.id, name)">
                  </InlineEditText>
                </div>
              </v-col>
              <v-col cols="1" class="col-container" :title="session.id">{{ session.id }}</v-col>
              <v-col cols="2" class="col-container" :title="session.createdDate | date">{{ session.createdDate | date }}</v-col>
              <v-col cols="1" class="col-container" :title="session.dataset.name ? session.dataset.name : 'Unnamed dataset'">{{ session.dataset.name ? session.dataset.name : 'Unnamed dataset' }}</v-col>

              <v-col cols="1" class="col-container" :title="session.dataset.id">{{ session.dataset.id }}</v-col>
              <v-col cols="2" class="col-container" :title="session.model.name">{{ session.model.name }}</v-col>
              <v-col cols="1" class="col-container" :title="session.dataset.id">{{ session.model.id }}</v-col>
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
      <div v-else>
        <router-view />
      </div>
    </v-container>

    <v-container v-else class="vc mt-6">
      <v-alert class="text-center">
        <p class="headline font-weight-medium grey--text text--darken-2">You haven't created any debugging session for this project. <br>Please create your first session to start debugging your model.</p>
      </v-alert>
      <AddDebuggingSessionModal :projectId="projectId" v-on:createDebuggingSession="createDebuggingSession"></AddDebuggingSessionModal>
      <div class="d-flex justify-center mb-6">
        <img src="@/assets/logo_debugger.png" class="debugger-logo" title="Debugger tab logo" alt="A turtle using a magnifying glass">
      </div>
    </v-container>
  </div>
  <v-container v-else class="d-flex flex-column vc fill-height">
    <h1 class="pt-16">ML Worker is not connected</h1>
    <StartWorkerInstructions></StartWorkerInstructions>
  </v-container>
</template>

<style scoped>
.debugger-logo {
  width: min(17.5vw, 200px);
  margin-top: 2rem;
}

.col-container {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.expansion-panel {
  margin-top: 10px !important;
}
</style>
