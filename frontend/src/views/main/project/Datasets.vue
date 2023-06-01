<template>
  <div class="vertical-container">
    <v-container class="mt-2 mb-0" v-if="isProjectOwnerOrAdmin">
      <div class="d-flex justify-end align-center">
        <v-btn tile small class="mx-2" href="https://docs.giskard.ai/start/guides/upload-your-model" target="_blank">
          Upload with API
        </v-btn>
        <v-btn text @click="loadDatasets()" color="secondary">Reload
          <v-icon right>refresh</v-icon>
        </v-btn>
      </div>
    </v-container>
    <v-container v-if="files.length > 0">
      <v-expansion-panels>
        <v-row dense no-gutters class="mr-12 ml-2 caption secondary--text text--lighten-3 pb-2">
          <v-col cols="4">Name</v-col>
          <v-col cols="1">Size</v-col>
          <v-col cols="2">Uploaded on</v-col>
          <v-col cols="2">Target</v-col>
          <v-col cols="1">Id</v-col>
          <v-col cols="2">Actions</v-col>
        </v-row>
        <v-expansion-panel v-for="f in files" :key="f.id">
          <v-expansion-panel-header @click="peakDataFile(f.id)" class="py-1 pl-2">
            <v-row dense no-gutters align="center">
              <v-col cols="4" class="font-weight-bold">
                <InlineEditText
                    :text="f.name"
                    :can-edit="isProjectOwnerOrAdmin"
                    @save="(name) => renameDataset(f.id, name)">
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
              <DeleteModal
                  v-if="isProjectOwnerOrAdmin"
                  :id="f.id"
                  :file-name="f.name"
                  type="dataset"
                  @submit="deleteDataFile(f.id)"
              />
            </span>
              </v-col>
            </v-row>

          </v-expansion-panel-header>
          <v-expansion-panel-content>
            <v-data-table :headers="filePreviewHeader" :items="filePreviewData"
                          dense :hide-default-footer="true"
                          v-if="filePreviewHeader.length > 0 && filePreviewData.length > 0">
            </v-data-table>
            <div class="caption" v-else>Could not properly load data</div>
          </v-expansion-panel-content>
        </v-expansion-panel>
      </v-expansion-panels>
    </v-container>
    <v-container v-else class="font-weight-light font-italic secondary--text">
      No files uploaded yet.
    </v-container>
  </div>
</template>

<script setup lang="ts">
import {api} from '@/api';
import {DatasetDTO} from '@/generated-sources';
import mixpanel from "mixpanel-browser";
import DeleteModal from '@/views/main/project/modals/DeleteModal.vue';
import {onActivated, ref} from 'vue';
import InlineEditText from '@/components/InlineEditText.vue';
import {useMainStore} from "@/stores/main";

const GISKARD_INDEX_COLUMN_NAME = '_GISKARD_INDEX_';

const props = withDefaults(defineProps<{
  projectId: number,
  isProjectOwnerOrAdmin: boolean
}>(), {
  isProjectOwnerOrAdmin: false
});

const files = ref<DatasetDTO[]>([]);
const lastVisitedFileId = ref<string | null>(null);
const filePreviewHeader = ref<{ text: string, value: string, sortable: boolean }[]>([]);
const filePreviewData = ref<any[]>([]);

onActivated(() => loadDatasets());

async function loadDatasets() {
  files.value = await api.getProjectDatasets(props.projectId)
  files.value.sort((a, b) => new Date(a.createdDate) < new Date(b.createdDate) ? 1 : -1);
}

async function deleteDataFile(id: string) {
  mixpanel.track('Delete dataset', {id});

  let messageDTO = await api.deleteDatasetFile(id);
  useMainStore().addNotification({content: messageDTO.message});
  await loadDatasets();
}

function downloadDataFile(id: string) {
  mixpanel.track('Download dataset file', {id});
  api.downloadDataFile(id)
}

async function peakDataFile(id: string) {
  if (lastVisitedFileId.value != id) {
    lastVisitedFileId.value = id; // this is a trick to avoid recalling the api every time one panel is opened/closed
    try {
      const response = await api.peekDataFile(id)
      const headers = Object.keys(response[0])
      filePreviewHeader.value = headers.filter(e => e != GISKARD_INDEX_COLUMN_NAME).map(e => {
        return {text: e.trim(), value: e, sortable: false}
      });
      if (headers.includes(GISKARD_INDEX_COLUMN_NAME)) {
        filePreviewHeader.value = [{
          text: '#',
          value: GISKARD_INDEX_COLUMN_NAME,
          sortable: false
        }].concat(filePreviewHeader.value);
      }
      filePreviewData.value = response
    } catch (error) {
      useMainStore().addNotification({content: error.response.statusText, color: 'error'});
      filePreviewHeader.value = [];
      filePreviewData.value = [];
    }
  }
}

async function renameDataset(id: string, name: string) {
  mixpanel.track('Update dataset name', {id});
  const savedDataset = await api.editDatasetName(id, name);
  const idx = files.value.findIndex(f => f.id === id);
  files.value[idx] = savedDataset;
  files.value = [...files.value];
}
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
</style>
