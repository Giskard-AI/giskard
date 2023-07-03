<template>
  <div>
    <div v-if='isMLWorkerConnected' class='vertical-container'>
      <v-container v-if='debuggingSessionsStore.debuggingSessions.length > 0' class='vc' fluid>
        <v-row>
          <v-col cols='4'>
            <v-text-field v-show='debuggingSessionsStore.currentDebuggingSessionId === null' v-model='searchSession' append-icon='search' label='Search for a debugging session' outlined></v-text-field>
          </v-col>
          <v-col cols='8'>
            <div class='d-flex justify-end'>
              <v-btn v-if='debuggingSessionsStore.currentDebuggingSessionId !== null' class='mr-3' text @click='showPastSessions'>
                <v-icon class='mr-2'>mdi-arrow-left</v-icon>
                Back to all sessions
              </v-btn>
              <AddDebuggingSessionModal v-show='debuggingSessionsStore.currentDebuggingSessionId === null' :projectId='projectId' @createDebuggingSession='createDebuggingSession'></AddDebuggingSessionModal>
            </div>
          </v-col>
        </v-row>

        <v-expansion-panels v-if='debuggingSessionsStore.currentDebuggingSessionId === null'>
          <v-row class='mr-12 ml-6 caption secondary--text text--lighten-3 pb-2'>
            <v-col class='col-container' cols='3' title='Session name'>Session name</v-col>
            <v-col class='col-container' cols='2' title='Created at'>Created at</v-col>
            <v-col class='col-container' cols='3' title='Dataset'>Dataset</v-col>
            <v-col class='col-container' cols='3' title='Model'>Model</v-col>
            <v-col cols='1'></v-col>
          </v-row>

          <v-expansion-panel v-for='session in filteredSessions' :key='session.id' class='expansion-panel' @click.stop='openDebuggingSession(session.id, projectId)'>
            <v-expansion-panel-header :disableIconRotate='true' class='grey lighten-5' tile>
              <v-row class='px-2 py-1 align-center'>
                <v-col :title='`${session.name} (ID: ${session.id})`' class='font-weight-bold' cols='3'>
                  <div class='pr-4'>
                    <InlineEditText :text='session.name' @save='(name) => renameSession(session.id, name)'>
                    </InlineEditText>
                  </div>
                </v-col>
                <v-col class='col-container' cols='2'>
                  <span :title='session.createdDate | date'>
                    {{ session.createdDate | date }}
                  </span>
                </v-col>
                <v-col class='col-container' cols='3'>
                  <span :title="(session.dataset.name ? session.dataset.name : 'Unnamed dataset') + ` (ID: ${session.dataset.id})`" @click.stop.prevent="copyText(session.dataset.id, 'Copied dataset ID to clipboard')">
                    {{ session.dataset.name ? session.dataset.name : 'Unnamed dataset' }}
                  </span>
                </v-col>
                <v-col class='col-container' cols='3'>
                  <span :title='`${session.model.name} (ID: ${session.model.id})`' @click.stop.prevent="copyText(session.model.id, 'Copied model ID to clipboard')">{{ session.model.name ? session.model.name : 'Unnamed model'
                  }}</span>
                </v-col>
                <v-col cols='1'>
                  <v-card-actions>
                    <v-btn icon @click.stop.prevent='deleteDebuggingSession(session)'>
                      <v-icon color='accent'>delete</v-icon>
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

      <v-container v-else class='vc mt-6'>
        <v-alert class='text-center'>
          <p class='headline font-weight-medium grey--text text--darken-2'>You haven't created any debugging session for
            this project. <br>Please create your first session to start debugging your model.</p>
        </v-alert>
        <AddDebuggingSessionModal :projectId='projectId' v-on:createDebuggingSession='createDebuggingSession'></AddDebuggingSessionModal>
        <div class='d-flex justify-center mb-6'>
          <img alt='A turtle using a magnifying glass' class='debugger-logo' src='@/assets/logo_debugger.png' title='Debugger tab logo'>
        </div>
      </v-container>
    </div>
    <v-container v-else class='d-flex flex-column align-center'>
      <h1 class='pt-16'>ML Worker is not connected</h1>
      <StartWorkerInstructions></StartWorkerInstructions>
    </v-container>
  </div>
</template>

<script lang='ts' setup>
import { computed, onActivated, ref, watch } from 'vue';
import { $vfm } from 'vue-final-modal';
import { api } from '@/api';
import { useRoute, useRouter } from 'vue-router/composables';
import { useMainStore } from '@/stores/main';
import { useDebuggingSessionsStore } from '@/stores/debugging-sessions';
import { InspectionDTO } from '@/generated-sources';
import AddDebuggingSessionModal from '@/components/AddDebuggingSessionModal.vue';
import InlineEditText from '@/components/InlineEditText.vue';
import ConfirmModal from './modals/ConfirmModal.vue';
import StartWorkerInstructions from '@/components/StartWorkerInstructions.vue';
import { copyText } from '@/utils';
import { TYPE } from 'vue-toastification';
import { state } from "@/socket";

const router = useRouter();
const route = useRoute();

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
});


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
  await openDebuggingSession(debuggingSession.id, props.projectId);
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
        useMainStore().addNotification({
          content: `The debugging session '${debuggingSession.name}' has been deleted.`,
          color: TYPE.SUCCESS,
          showProgress: false
        });
      }
    }
  });
}

async function openDebuggingSession(debuggingSessionId: number, projectId: number) {
  debuggingSessionsStore.setCurrentDebuggingSessionId(debuggingSessionId);
  await openInspection(projectId.toString(), debuggingSessionId.toString());
}

function resetSearchInput() {
  searchSession.value = '';
}

async function openInspection(projectId: string, inspectionId: string) {
  await router.push({
    name: 'inspection',
    params: {
      id: projectId,
      inspectionId: inspectionId
    }
  });
}

watch(() => debuggingSessionsStore.currentDebuggingSessionId, async (currentDebuggingSessionId) => {
  if (currentDebuggingSessionId !== null) {
    await openInspection(props.projectId.toString(), currentDebuggingSessionId.toString());
  }
});


watch(() => route.name, async (name) => {
  if (name === 'project-debugger') {
    await debuggingSessionsStore.reload();
    resetSearchInput();
    debuggingSessionsStore.setCurrentDebuggingSessionId(null);
  }
});

onActivated(async () => {
  await debuggingSessionsStore.loadDebuggingSessions(props.projectId);

  if (route.params.inspectionId !== undefined) {
    debuggingSessionsStore.setCurrentDebuggingSessionId(parseInt(route.params.inspectionId));
  }

  if (debuggingSessionsStore.currentDebuggingSessionId !== null) {
    await openInspection(props.projectId.toString(), debuggingSessionsStore.currentDebuggingSessionId.toString());
  }
});
</script>

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

::v-deep .v-toolbar__content {
  padding-left: 4px !important;
  display: inline-flex;
  flex-direction: column;
}
</style>
