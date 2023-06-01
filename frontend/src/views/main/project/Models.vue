<template>
  <div class="vertical-container">
    <div class="d-flex mb-6">
      <v-spacer></v-spacer>
      <v-btn @click="reloadModels">
        Reload
        <v-icon right>refresh</v-icon>
      </v-btn>
      <v-btn color="primary" class="mx-2" href="https://docs.giskard.ai/start/guides/upload-your-model" target="_blank">
        Upload with API
        <v-icon right>mdi-application-braces-outline</v-icon>
      </v-btn>
    </div>
    <v-container v-if="projectArtifactsStore.models.length > 0" fluid class="vc">
      <v-card flat>
        <v-row class="px-2 py-1 caption secondary--text text--lighten-3">
          <v-col cols="3">Name</v-col>
          <v-col cols="2">Python</v-col>
          <v-col cols="1">Size</v-col>
          <v-col cols="2">Uploaded on</v-col>
          <v-col cols="1">Id</v-col>
          <v-col cols="3">Actions</v-col>
        </v-row>
      </v-card>
      <v-card class="grey lighten-5" v-for="m in        projectArtifactsStore.models      " :key="m.id" outlined tiled>
        <v-row class="px-2 py-1 align-center">
          <v-col cols="3" class="font-weight-bold">
            <InlineEditText :text="m.name" :can-edit="isProjectOwnerOrAdmin" @save="(name) => renameModel(m.id, name)">
            </InlineEditText>
          </v-col>
          <v-col cols="2">
            <div>{{ m.languageVersion }}</div>
          </v-col>
          <v-col cols="1">
            <div>{{ m.size | fileSize }}</div>
          </v-col>
          <v-col cols="2">
            <div>{{ m.createdDate | date }}</div>
          </v-col>
          <v-col cols="1" class="id-container" :title="m.id">
            {{ m.id }}
          </v-col>
          <v-col cols="3">
            <div>
              <v-btn small tile color="primaryLight" class="primaryLightBtn" @click="showInspectDialog = true; modelToInspect = m">
                <v-icon dense left>policy</v-icon>
                Debug
              </v-btn>
              <v-tooltip bottom>
                <template v-slot:activator="{ on, attrs }">
                  <v-btn icon color="info" @click=" downloadModelPickle(m.id)" v-bind="attrs" v-on="on">
                    <v-icon>download</v-icon>
                  </v-btn>
                </template>
                <span>Download</span>
              </v-tooltip>
              <DeleteModal v-if="isProjectOwnerOrAdmin" :id="m.id" :file-name="m.fileName" type="model" @submit=" deleteModelPickle(m.id)" />
            </div>
          </v-col>
        </v-row>
        <v-divider></v-divider>
      </v-card>

      <!-- Dialog for launching model inspection -->
      <v-dialog persistent max-width="600" v-model="showInspectDialog" class="inspector-launcher-container">
        <InspectorLauncher :projectId="projectId" :model="modelToInspect" @cancel=" cancelLaunchInspector()" />
      </v-dialog>

    </v-container>
    <v-container v-if="projectArtifactsStore.models.length === 0 && apiAccessToken && apiAccessToken.id_token">
      <p class="font-weight-medium secondary--text">There are no models in this project yet. Follow the code snippet below to upload a model 👇</p>
      <CodeSnippet :code-content="codeContent" :language="'python'"></CodeSnippet>
      <p class="mt-4 font-weight-medium secondary--text">Check out the <a href="https://docs.giskard.ai/start/~/changes/QkDrbY9gX75RDMmAWKjX/guides/upload-your-model#2.-create-a-giskard-model" target="_blank">full documentation</a> for more information.</p>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { api } from '@/api';
import { apiURL } from "@/env";
import { Role } from "@/enums";
import InspectorLauncher from './InspectorLauncher.vue';
import { JWTToken, ModelDTO } from '@/generated-sources';
import mixpanel from "mixpanel-browser";
import { onBeforeMount, onMounted, ref, computed } from 'vue';
import DeleteModal from '@/views/main/project/modals/DeleteModal.vue';
import InlineEditText from '@/components/InlineEditText.vue';
import { useUserStore } from "@/stores/user";
import { useProjectStore } from "@/stores/project";
import { useMainStore } from "@/stores/main";
import { useProjectArtifactsStore } from "@/stores/project-artifacts";
import CodeSnippet from '@/components/CodeSnippet.vue';

const userStore = useUserStore();
const projectStore = useProjectStore();
const projectArtifactsStore = useProjectArtifactsStore();

interface Props {
  projectId: number,
}

const props = defineProps<Props>();

const showInspectDialog = ref<boolean>(false);
const modelToInspect = ref<ModelDTO | null>(null);
const apiAccessToken = ref<JWTToken | null>(null);

const codeContent = computed(
// language=Python
    () =>
  `from giskard import Model, GiskardClient
from giskard.demo import titanic  # for demo purposes only 🛳️

original_model, _ = titanic()  # Replace with your model creation

# Create a Giskard client
token = "${apiAccessToken.value!.id_token}"
client = GiskardClient(
    url="${apiURL}",  # URL of your Giskard instance
    token=token
)

# Wrap your model with Giskard model
giskard_model = Model(original_model, model_type="classification", name="Titanic model")

# Upload to the current project
giskard_model.upload(client, "${project.value!.key}")`
)

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

function downloadModelPickle(id: number) {
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
  await projectArtifactsStore.loadModelsWithNotification();
}

const generateApiAccessToken = async () => {
  try {
    apiAccessToken.value = await api.getApiAccessToken();
  } catch (error) {
    console.log(error);
  }
}

onBeforeMount(async () => {
  await projectArtifactsStore.setProjectId(props.projectId, false);
})

onMounted(async () => {
  if (projectArtifactsStore.models.length === 0) await generateApiAccessToken();
})
</script>

<style>
div.v-dialog {
  overflow-y: hidden;
}

.id-container {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
