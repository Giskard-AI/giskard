<template>
  <div class="vertical-container">
    <v-container v-if="projectArtifactsStore.datasets.length > 0" fluid class="vc">
      <v-expansion-panels flat>
        <v-row dense no-gutters class="mr-6 ml-3 caption secondary--text text--lighten-3 pb-2">
          <v-col cols="4">Name</v-col>
          <v-col cols="1">Size</v-col>
          <v-col cols="2">Uploaded on</v-col>
          <v-col cols="2">Target</v-col>
          <v-col cols="1">Id</v-col>
          <v-col cols="2">Actions</v-col>
        </v-row>
        <v-expansion-panel v-for="f in projectArtifactsStore.datasets" :key="f.id">
          <v-expansion-panel-header @click="peakDataFile(f.id)" class="grey lighten-5 py-1 pl-2">
            <v-row class="px-2 py-1 align-center">
              <v-col cols="4" class="font-weight-bold">
                <InlineEditText :text="f.name" :can-edit="isProjectOwnerOrAdmin" @save="(name) => renameDataset(f.id, name)">
                </InlineEditText>
              </v-col>
              <v-col cols="1">{{ f.originalSizeBytes | fileSize }}</v-col>
              <v-col cols="2">{{ f.createdDate | date }}</v-col>
              <v-col cols="2">{{ f.target }}</v-col>
              <v-col cols="1" class="id-container" :title="f.id"> {{ f.id }}</v-col>
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
    <v-container v-else>
      <p class="font-weight-medium secondary--text">There are no datasets in this project yet. Follow the code snippet below to upload a dataset 👇</p>
      <CodeSnippet :code-content="codeContent" :language="'python'"></CodeSnippet>
      <p class="mt-4 font-weight-medium secondary--text">Check out the <a href="https://docs.giskard.ai/start/~/changes/QkDrbY9gX75RDMmAWKjX/guides/upload-your-model#3.-create-a-giskard-dataset" target="_blank">full documentation</a> for more information.</p>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { api } from '@/api';
import mixpanel from "mixpanel-browser";
import DeleteModal from '@/views/main/project/modals/DeleteModal.vue';
import { computed, onBeforeMount, ref } from 'vue';
import InlineEditText from '@/components/InlineEditText.vue';
import { useMainStore } from "@/stores/main";
import { useProjectArtifactsStore } from "@/stores/project-artifacts";
import CodeSnippet from '@/components/CodeSnippet.vue';

const projectArtifactsStore = useProjectArtifactsStore();

const GISKARD_INDEX_COLUMN_NAME = '_GISKARD_INDEX_';

const props = withDefaults(defineProps<{
  projectId: number,
  projectKey: string,
  isProjectOwnerOrAdmin: boolean
}>(), {
  isProjectOwnerOrAdmin: false
});

const lastVisitedFileId = ref<string | null>(null);
const filePreviewHeader = ref<{ text: string, value: string, sortable: boolean }[]>([]);
const filePreviewData = ref<any[]>([]);

const codeContent = computed(() =>
  `# Create a Giskard client
from giskard import GiskardClient
url = "http://localhost:19000" # URL of your Giskard instance
token = "my_API_Access_Token" # Your API Access Token (generate one in Settings > API Access Token > Generate)
client = GiskardClient(url, token)

# Load your data (example: from a csv file as a pandas dataframe)
import pandas as pd
my_df = pd.read_csv("data.csv")
my_column_types = {"categorical_column": "category",
                   "text_column": "text",
                   "numeric_column": "numeric"} # Declare the type of each column in your data (example: category, numeric, text)

# Create a Giskard Dataset
from giskard import Dataset
my_dataset = Dataset(df=my_df, 
                     target="numeric_column",
                     column_types=my_column_types,
                     name="My Dataset")

# Upload your dataset on Giskard
project_key = "${props.projectKey}" # Current project key
my_dataset.upload(client, project_key)`
)


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
      useMainStore().addNotification({ content: error.response.statusText, color: 'error' });
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

onBeforeMount(async () => {
  await projectArtifactsStore.setProjectId(props.projectId);
})
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

.id-container {
  overflow: hidden;
  text-overflow: ellipsis;
}

.expansion-panel-content::v-deep .v-expansion-panel-content__wrap {
  padding: 0 0 16px !important;
}
</style>
