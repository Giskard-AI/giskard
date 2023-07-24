<template>
  <div class="vertical-container">
    <v-row class="mt-2 pl-3">
      <v-col cols='4'>
        <v-text-field v-if="projectArtifactsStore.models.length" v-model='searchModel' append-icon='search' label='Search for a model' outlined></v-text-field>
      </v-col>
      <v-col cols="8">
        <div class="d-flex justify-end mb-6">
          <v-btn v-if="projectArtifactsStore.models.length > 0" class="mr-2" href="https://docs.giskard.ai/en/latest/guides/wrap_model/index.html" target="_blank" rel="noopener">
            add a model
            <v-icon right>mdi-open-in-new</v-icon>
          </v-btn>
        </div>
      </v-col>
    </v-row>
    <LoadingFullscreen v-if="isLoading" name="models" />
    <v-container v-if="projectArtifactsStore.models.length > 0 && !isLoading" fluid class="vc">
      <v-card flat>
        <v-row class="px-2 py-1 caption secondary--text text--lighten-3">
          <v-col cols="3" class="col-container">Name</v-col>
          <v-col cols="2" class="col-container">Python</v-col>
          <v-col cols="1" class="col-container">Size</v-col>
          <v-col cols="2" class="col-container">Uploaded on</v-col>
          <v-col cols="1" class="col-container">Id</v-col>
          <v-col cols="3" class="col-container">Actions</v-col>
        </v-row>
      </v-card>
      <v-card class="grey lighten-5" v-for="m in filteredModels" :key="m.id" outlined tiled>
        <v-row class="px-2 py-1 align-center">
          <v-col cols="3" class="font-weight-bold" :title="m.name">
            <InlineEditText :text="m.name" :can-edit="isProjectOwnerOrAdmin" @save="(name) => renameModel(m.id, name)">
            </InlineEditText>
          </v-col>
          <v-col cols="2" class="col-container" :title="m.languageVersion">
            {{ m.languageVersion }}
          </v-col>
          <v-col cols="1" class="col-container" :title="m.size | fileSize">
            {{ m.size | fileSize }}
          </v-col>
          <v-col cols="2" class="col-container" :title="m.createdDate | date">
            {{ m.createdDate | date }}
          </v-col>
          <v-col cols="1" class="col-container" :title="m.id">
            {{ m.id }}
          </v-col>
          <v-col cols="3">
            <div>
              <v-btn small tile color="primaryLight" class="primaryLightBtn mr-1" @click="showInspectDialog = true; modelToInspect = m">
                <v-icon dense left>policy</v-icon>
                Debug
              </v-btn>
              <v-tooltip bottom>
                <template v-slot:activator="{ on, attrs }">
                  <v-btn icon @click=" downloadModelPickle(m.id)" v-bind="attrs" v-on="on">
                    <v-icon>download</v-icon>
                  </v-btn>
                </template>
                <span>Download</span>
              </v-tooltip>
              <DeleteModal v-if="isProjectOwnerOrAdmin" :id="m.id" :file-name="m.name" type="model" @submit=" deleteModelPickle(m.id)" />
            </div>
          </v-col>
        </v-row>
        <v-divider></v-divider>
      </v-card>

      <div class="d-flex flex-column align-center justify-center mt-6">
        <v-btn small @click="reloadModels" plain>
          <span class="caption">Refresh</span>
          <v-icon size="small" class="ml-1">refresh</v-icon>
        </v-btn>
      </div>

      <!-- Dialog for launching model inspection -->
      <v-dialog v-if="isMLWorkerConnected" v-model="showInspectDialog" @click:outside="cancelLaunchInspector" max-width="600">
        <InspectorLauncher :projectId="projectId" :model="modelToInspect" @cancel="cancelLaunchInspector"></InspectorLauncher>
      </v-dialog>
      <v-dialog v-else v-model="showInspectDialog" @click:outside="cancelLaunchInspector" max-width="1000">
        <v-card>
          <v-card-title class="py-6">
            <h2>ML Worker is not connected</h2>
          </v-card-title>
          <v-card-text>
            <StartWorkerInstructions></StartWorkerInstructions>
          </v-card-text>
          <v-card-actions>
            <v-btn text @click="cancelLaunchInspector">Close</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>

    </v-container>
    <v-container v-else-if="!isLoading">
      <v-alert class='text-center'>
        <p class='headline font-weight-medium grey--text text--darken-2'>There are no models in this project yet. <br>Click the button below to learn how to upload a model.</p>
      </v-alert>
      <div class="d-flex justify-center">
        <v-btn href="https://docs.giskard.ai/en/latest/guides/wrap_model/index.html" target="_blank" rel="noopener">
          add a new model
          <v-icon right>mdi-open-in-new</v-icon>
        </v-btn>
      </div>
      <div class="d-flex justify-center mb-6">
        <img src="@/assets/logo_models.png" class="models-logo" title="Models tab logo" alt="A turtle drinking coffee and using a laptop">
      </div>
      <div class="d-flex justify-center mt-6">
        <v-btn small @click="reloadModels" plain>
          <span class="caption">Refresh</span>
          <v-icon size="small" class="ml-1">refresh</v-icon>
        </v-btn>
      </div>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import {api} from '@/api';
import {Role} from "@/enums";
import InspectorLauncher from './InspectorLauncher.vue';
import {ModelDTO} from '@/generated-sources';
import mixpanel from "mixpanel-browser";
import { computed, onBeforeMount, ref } from 'vue';
import DeleteModal from '@/views/main/project/modals/DeleteModal.vue';
import InlineEditText from '@/components/InlineEditText.vue';
import {useUserStore} from "@/stores/user";
import {useProjectStore} from "@/stores/project";
import {useMainStore} from "@/stores/main";
import {useProjectArtifactsStore} from "@/stores/project-artifacts";
import LoadingFullscreen from "@/components/LoadingFullscreen.vue";
import {state} from "@/socket";
import StartWorkerInstructions from "@/components/StartWorkerInstructions.vue";
import {generateGiskardClientSnippet} from "@/snippets";


const userStore = useUserStore();
const projectStore = useProjectStore();
const projectArtifactsStore = useProjectArtifactsStore();

interface Props {
  projectId: number,
}

const props = defineProps<Props>();

const isLoading = ref<boolean>(false);
const showInspectDialog = ref<boolean>(false);
const modelToInspect = ref<ModelDTO | null>(null);
const searchModel = ref<string>('');

const filteredModels = computed(() => {
  return projectArtifactsStore.models.filter((model) => {
    const search = searchModel.value.toLowerCase();
    return (
      model.name.toLowerCase().includes(search) ||
      model.id.toString().includes(search)
    );
  });
});

const isMLWorkerConnected = computed(() => {
  return state.workerStatus.connected;
});

const project = computed(() => {
  return projectStore.project(props.projectId)
});

const userProfile = computed(() => {
  return userStore.userProfile;
});

const isProjectOwnerOrAdmin = computed(() => {
  return isUserProjectOwner.value || userProfile.value?.roles?.includes(Role.ADMIN)
});

const isUserProjectOwner = computed(() => {
  return project.value && userProfile.value ? project.value?.owner.id == userProfile.value?.id : false;
});

async function deleteModelPickle(id: string) {
  mixpanel.track('Delete model', { id });

  let messageDTO = await api.deleteModelFiles(id);
  useMainStore().addNotification({ content: messageDTO.message });
  await projectArtifactsStore.loadModels();
}

function downloadModelPickle(id: string) {
  mixpanel.track('Download model', { id });
  api.downloadModelFile(id)
}

function cancelLaunchInspector() {
  showInspectDialog.value = false;
}

async function renameModel(id: string, name: string) {
  mixpanel.track('Update model name', { id });
  const savedModel = await api.editModelName(id, name);
  projectArtifactsStore.updateModel(savedModel);
}

async function reloadModels() {
  isLoading.value = true;
  try {
    await projectArtifactsStore.loadModels();
  } finally {
    isLoading.value = false;
  }
}

onBeforeMount(async () => {
  await projectArtifactsStore.setProjectId(props.projectId, false);
});
</script>

<style>
div.v-dialog {
  overflow-y: hidden;
}

.col-container {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.models-logo {
  height: max(50vh, 150px);
  margin-top: 2rem;
}
</style>
