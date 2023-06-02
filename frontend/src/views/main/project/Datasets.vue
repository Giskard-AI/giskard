<template>
  <div class="vertical-container">
    <div class="d-flex mb-6">
      <v-spacer></v-spacer>
      <div class="mr-2">
        <v-btn @click="reloadDatasets">
          Reload
          <v-icon right>refresh</v-icon>
        </v-btn>
        <v-btn v-if="projectArtifactsStore.datasets.length > 0" color="primary" class="ml-2" @click="openUploadDialog">
          Upload with API
          <v-icon right>mdi-application-braces-outline</v-icon>
        </v-btn>
      </div>
    </div>
    <LoadingFullscreen v-if="isLoading" name="datasets" />
    <v-container v-if="projectArtifactsStore.datasets.length > 0 && !isLoading" fluid class="vc">
      <v-expansion-panels flat>
        <v-row dense no-gutters class="mr-6 ml-3 caption secondary--text text--lighten-3 pb-2">
          <v-col cols="4" class="col-container">Name</v-col>
          <v-col cols="1" class="col-container">Size</v-col>
          <v-col cols="2" class="col-container">Uploaded on</v-col>
          <v-col cols="2" class="col-container">Target</v-col>
          <v-col cols="1" class="col-container">Id</v-col>
          <v-col cols="2" class="col-container">Actions</v-col>
        </v-row>
        <v-expansion-panel v-for="f in projectArtifactsStore.datasets" :key="f.id">
          <v-expansion-panel-header @click="peakDataFile(f.id)" class="grey lighten-5 py-1 pl-2">
            <v-row class="px-2 py-1 align-center">
              <v-col cols="4" class="font-weight-bold" :title="f.name ? f.name : f.id">
                <InlineEditText :text="f.name ? f.name : 'Unnamed dataset'" :can-edit="isProjectOwnerOrAdmin" @save="(name) => renameDataset(f.id, name)">
                </InlineEditText>
              </v-col>
              <v-col cols="1" class="col-container" :title="f.originalSizeBytes | fileSize">{{ f.originalSizeBytes | fileSize }}</v-col>
              <v-col cols="2" class="col-container" :title="f.createdDate | date">{{ f.createdDate | date }}</v-col>
              <v-col cols="2" class="col-container" :title="f.target">{{ f.target }}</v-col>
              <v-col cols="1" class="col-container" :title="f.id"> {{ f.id }}</v-col>
              <v-col cols="2">
                <span>
                  <v-tooltip bottom dense>
                    <template v-slot:activator="{ on, attrs }">
                      <v-btn icon color="info" @click.stop="downloadDataFile(f.id)" v-bind="attrs" v-on="on">
                        <v-icon>download</v-icon>
                      </v-btn>
                    </template>
                    <span>Download</span>
                  </v-tooltip>
                  <DeleteModal v-if="isProjectOwnerOrAdmin" :id="f.id" :file-name="f.name" type="dataset" @submit="deleteDataFile(f.id)" />
                </span>
              </v-col>
            </v-row>
          </v-expansion-panel-header>
          <v-divider></v-divider>
          <v-expansion-panel-content class="expansion-panel-content">
            <v-data-table :headers="filePreviewHeader" :items="filePreviewData" dense :hide-default-footer="true" v-if="filePreviewHeader.length > 0 && filePreviewData.length > 0">
            </v-data-table>
            <div class="caption" v-else>Could not properly load data</div>
          </v-expansion-panel-content>
        </v-expansion-panel>
      </v-expansion-panels>
    </v-container>
    <v-container v-if="projectArtifactsStore.datasets.length === 0 && apiAccessToken && apiAccessToken.id_token && !isLoading">
      <p class="font-weight-medium secondary--text">There are no datasets in this project yet. Follow the code snippet below to upload a dataset 👇</p>
      <CodeSnippet :code-content="codeContent" :language="'python'"></CodeSnippet>
      <p class="mt-4 font-weight-medium secondary--text">Check out the <a href="https://docs.giskard.ai/en/latest/guides/wrap_dataset/index.html" target="_blank" rel="noopener">full documentation</a> for more information.</p>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { apiURL } from "@/env";
import { api } from "@/api";
import { Role } from "@/enums";
import { $vfm } from 'vue-final-modal';
import mixpanel from "mixpanel-browser";
import DeleteModal from "@/views/main/project/modals/DeleteModal.vue";
import { computed, onBeforeMount, onMounted, ref } from "vue";
import InlineEditText from "@/components/InlineEditText.vue";
import { useUserStore } from "@/stores/user";
import { useProjectStore } from "@/stores/project";
import { useMainStore } from "@/stores/main";
import { useProjectArtifactsStore } from "@/stores/project-artifacts";
import CodeSnippet from '@/components/CodeSnippet.vue';
import { JWTToken } from "@/generated-sources";
import { TYPE } from "vue-toastification";
import UploadArtifactModal from "./modals/UploadArtifactModal.vue";
import LoadingFullscreen from "@/components/LoadingFullscreen.vue";

const userStore = useUserStore();
const projectStore = useProjectStore();
const projectArtifactsStore = useProjectArtifactsStore();

const GISKARD_INDEX_COLUMN_NAME = '_GISKARD_INDEX_';

interface Props {
  projectId: number,
}

const props = defineProps<Props>();

const isLoading = ref<boolean>(false);
const lastVisitedFileId = ref<string | null>(null);
const filePreviewHeader = ref<{ text: string, value: string, sortable: boolean }[]>([]);
const filePreviewData = ref<any[]>([]);
const apiAccessToken = ref<JWTToken | null>(null);

const codeContent = computed(() =>
  `from giskard import Dataset, GiskardClient
from giskard.demo import titanic  # for demo purposes only 🛳️

_, df = titanic()  # Replace with your dataframe creation

# Create a Giskard client
token = "${apiAccessToken.value?.id_token}"
client = GiskardClient(
    url="${apiURL}",  # URL of your Giskard instance
    token=token
)

# Wrap your Pandas Dataframe with Giskard dataset 🎁
giskard_dataset = Dataset(df,
                          target="Survived",
                          name="Titanic dataset")

# Upload to the current project ✉️
giskard_dataset.upload(client, "${project.value!.key}")`
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

function openUploadDialog() {
  $vfm.show({
    component: UploadArtifactModal,
    bind: {
      title: 'Upload a dataset',
      codeContent: codeContent.value,
    },
  });
}

async function deleteDataFile(id: string) {
  mixpanel.track('Delete dataset', { id });

  let messageDTO = await api.deleteDatasetFile(id);
  useMainStore().addNotification({ content: messageDTO.message });
  await projectArtifactsStore.loadDatasets();
}

function downloadDataFile(id: string) {
  mixpanel.track('Download dataset file', { id });
  api.downloadDataFile(id)
}

async function peakDataFile(id: string) {
  if (lastVisitedFileId.value != id) {
    lastVisitedFileId.value = id; // this is a trick to avoid recalling the api every time one panel is opened/closed
    try {
      const response = await api.peekDataFile(id)
      const headers = Object.keys(response.content[0])
      filePreviewHeader.value = headers.filter(e => e != GISKARD_INDEX_COLUMN_NAME).map(e => {
        return { text: e.trim(), value: e, sortable: false }
      });
      if (headers.includes(GISKARD_INDEX_COLUMN_NAME)) {
        filePreviewHeader.value = [{
          text: '#',
          value: GISKARD_INDEX_COLUMN_NAME,
          sortable: false
        }].concat(filePreviewHeader.value);
      }
      filePreviewData.value = response.content
    } catch (error) {
      useMainStore().addNotification({ content: error.response.statusText, color: TYPE.ERROR });
      filePreviewHeader.value = [];
      filePreviewData.value = [];
    }
  }
}

async function renameDataset(id: string, name: string) {
  mixpanel.track('Update dataset name', { id });
  const savedDataset = await api.editDatasetName(id, name);
  projectArtifactsStore.updateDataset(savedDataset);
}

async function reloadDatasets() {
  isLoading.value = true;
  try {
    await projectArtifactsStore.loadDatasets();
  } finally {
    isLoading.value = false;
  }
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
});

onMounted(async () => {
  if (projectArtifactsStore.datasets.length === 0) await generateApiAccessToken();
});
</script>

<style lang="scss" scoped>
::v-deep .v-data-table__wrapper .v-data-table-header [role='columnheader'] {
  user-select: auto;
}

.file-xl {
  border-left: 4px solid #4CAF50
}

.file-csv {
  border-left: 4px solid #03A9F4
}

div.v-input {
  width: 400px;
}

.col-container {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.expansion-panel-content::v-deep .v-expansion-panel-content__wrap {
  padding: 0 0 16px !important;
}
</style>
