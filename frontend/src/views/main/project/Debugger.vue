<script setup lang="ts">
import { api } from '@/api';
import { InspectionDTO } from "@/generated-sources";
import AddDebuggingSession from '@/components/AddDebuggingSession.vue';
import InspectorWrapper from './InspectorWrapper.vue';
import { computed, ref, onActivated } from "vue";

interface Props {
  projectId: number;
  activeSessionId: number | null;
}

const props = withDefaults(defineProps<Props>(), {
  activeSessionId: null
});

const debuggingSessions = ref<InspectionDTO[]>([]);
const searchSession = ref("");

const displayComponents = computed(() => props.activeSessionId === null);

const filteredSessions = computed(() => {
  if (searchSession.value.length == 0) return orderByDate(debuggingSessions.value);

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

async function loadDebuggingSessions() {
  debuggingSessions.value = await api.getProjectInspections(props.projectId)
}


function toggleActiveSession(newActiveSessionId: Props["activeSessionId"]) {
  if (props.activeSessionId === newActiveSessionId) {
    props.activeSessionId = null;
  } else {
    props.activeSessionId = newActiveSessionId;
  }
}

function createDebuggingSession(debuggingSession: InspectionDTO) {
  debuggingSessions.value.push(debuggingSession);
  toggleActiveSession(null);
  setTimeout(() => {
    toggleActiveSession(debuggingSession.id);
  });
}

async function deleteDebuggingSession(id: number) {
  await api.deleteInspection(id);
  await loadDebuggingSessions();

}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);

  return date.getFullYear() +
    "-" + (date.getMonth() + 1).toString().padStart(2, "0") +
    "-" + date.getDate().toString().padStart(2, "0") +
    " " + date.getHours().toString().padStart(2, "0") +
    ":" + date.getMinutes().toString().padStart(2, "0");
}

function orderByDate(debuggingSessions: InspectionDTO[]): InspectionDTO[] {
  return debuggingSessions.sort((a, b) => {
    const aDate = new Date(a.createdDate);
    const bDate = new Date(b.createdDate);

    return bDate.getTime() - aDate.getTime();
  });
}

onActivated(() => loadDebuggingSessions());
</script>

<template>
  <div class="vertical-container">
    <v-container fluid class="vc" v-if="debuggingSessions.length > 0">
      <v-row>
        <v-col cols="4">
          <v-text-field v-show="displayComponents" label="Search for a debugging session" append-icon="search" outlined v-model="searchSession"></v-text-field>
        </v-col>
        <v-col cols="8">
          <div class="d-flex justify-end">
            <v-btn v-if="!displayComponents" @click="toggleActiveSession(null)" class="mr-4 pa-2 text--secondary">
              <v-icon>history</v-icon> Past sessions
            </v-btn>
            <AddDebuggingSession v-bind:project-id="projectId" v-on:createDebuggingSession="createDebuggingSession"></AddDebuggingSession>
          </div>
        </v-col>
      </v-row>

      <v-expansion-panels>
        <v-row dense no-gutters class="mr-12 ml-6 caption secondary--text text--lighten-3 pb-2" v-if="displayComponents">
          <v-col cols="3">Session name</v-col>
          <v-col cols="1">Session ID</v-col>
          <v-col cols="2">Created at</v-col>
          <v-col cols="1">Dataset name</v-col>
          <v-col cols="1">Dataset ID</v-col>
          <v-col cols="2">Model name</v-col>
          <v-col cols="1">Model ID</v-col>
          <v-col cols="1">Actions</v-col>
        </v-row>

        <v-expansion-panel v-for="session in filteredSessions" :key="session.id" v-show="displayComponents" @click="toggleActiveSession(session.id)">
          <v-expansion-panel-header :disableIconRotate="true">
            <v-row dense no-gutters class="align-center">
              <v-col cols="3">{{ session.name }}</v-col>
              <v-col cols="1">{{ session.id }}</v-col>
              <v-col cols="2">{{ formatDate(session.createdDate) }}</v-col>
              <v-col cols="1">{{ session.dataset.name }}</v-col>
              <v-col cols="1" class="id-container" :title="session.dataset.id">{{ session.dataset.id }}</v-col>
              <v-col cols="2">{{ session.model.name }}</v-col>
              <v-col cols="1" class="id-container" :title="session.dataset.id">{{ session.model.id }}</v-col>
              <v-col cols="1">
                <v-card-actions>
                  <v-btn icon color="accent" class="delete-button" @click.stop="deleteDebuggingSession(session.id)">
                    <v-icon>mdi-delete</v-icon>
                  </v-btn>
                </v-card-actions>
              </v-col>
            </v-row>
          </v-expansion-panel-header>
        </v-expansion-panel>
      </v-expansion-panels>
      <InspectorWrapper v-if="!displayComponents" :projectId="projectId" :inspectionId="activeSessionId"></InspectorWrapper>
    </v-container>

    <v-container v-else class="vc mt-12">
      <v-alert class="text-center">
        <p class="create-session-message headline blue-grey--text">You haven't created any debugging session for this project. <br>Please create your first session to start debugging your model.</p>
      </v-alert>
      <AddDebuggingSession v-bind:project-id="projectId" v-on:createDebuggingSession="createDebuggingSession"></AddDebuggingSession>
      <div class="d-flex justify-center mb-6">
        <img src="@/assets/logo_debugger.png" class="debugger-logo" title="Debugger tab logo" alt="A turtle using a magnifying glass">
      </div>
    </v-container>
  </div>
</template>

<style scoped>
.create-session-message {
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