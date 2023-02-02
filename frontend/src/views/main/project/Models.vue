<template>
  <div class="vertical-container">
    <v-container class="mt-2 mb-0" v-if="isProjectOwnerOrAdmin">
      <div class="d-flex justify-end align-center">
        <v-btn tile small class="mx-2" href="https://docs.giskard.ai/start/guides/upload-your-model" target="_blank">
          Upload with API
        </v-btn>
        <v-btn text @click="loadModelPickles()" color="secondary">Reload
          <v-icon right>refresh</v-icon>
        </v-btn>
      </div>
    </v-container>
    <v-container v-if="models.length > 0">
      <v-card flat>
        <v-row class="px-2 py-1 caption secondary--text text--lighten-3">
          <v-col cols="4">Name</v-col>
          <v-col cols="1">Python</v-col>
          <v-col cols="1">Size</v-col>
          <v-col cols="2">Uploaded on</v-col>
          <v-col cols="1">Id</v-col>
          <v-col cols="3">Actions</v-col>
        </v-row>
      </v-card>
      <v-card outlined tile class="grey lighten-5" v-for="m in models" :key="m.id">
        <v-row class="px-2 py-1 align-center">
          <v-col cols="4">
            <InlineEditText
                :text="m.name"
                :can-edit="isProjectOwnerOrAdmin"
                @save="(name) => renameModel(m.id, name)">
            </InlineEditText>
          </v-col>
          <v-col cols="1">
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
              <v-btn small tile color="primary"
                     @click="showInspectDialog = true; modelToInspect = m">
                <v-icon dense left>policy</v-icon>
                Inspect
              </v-btn>
              <v-tooltip bottom>
                <template v-slot:activator="{ on, attrs }">
                  <v-btn icon color="info" @click="downloadModelPickle(m.id)" v-bind="attrs" v-on="on">
                    <v-icon>download</v-icon>
                  </v-btn>
                </template>
                <span>Download</span>
              </v-tooltip>
              <DeleteModal
                  v-if="isProjectOwnerOrAdmin"
                  :id="m.id"
                  :file-name="m.fileName"
                  type="model"
                  @submit="deleteModelPickle(m.id)"
              />
            </div>
          </v-col>
        </v-row>
        <v-divider></v-divider>
      </v-card>

      <!-- Dialog for launching model inspection -->
      <v-dialog persistent max-width="600" v-model="showInspectDialog" class="inspector-launcher-container">
        <InspectorLauncher :projectId="projectId" :model="modelToInspect"
                           @cancel="cancelLaunchInspector()"/>
      </v-dialog>

    </v-container>
    <v-container v-else class="font-weight-light font-italic secondary--text">
      No models uploaded yet.
    </v-container>
  </div>
</template>

<script setup lang="ts">
import {api} from '@/api';
import InspectorLauncher from './InspectorLauncher.vue';
import {ModelDTO} from '@/generated-sources';
import mixpanel from "mixpanel-browser";
import {onActivated, ref} from 'vue';
import DeleteModal from '@/views/main/project/modals/DeleteModal.vue';
import {commitAddNotification} from '@/store/main/mutations';
import store from '@/store';
import InlineEditText from '@/components/InlineEditText.vue';

const props = withDefaults(defineProps<{
  projectId: number,
  isProjectOwnerOrAdmin: boolean
}>(), {
  isProjectOwnerOrAdmin: false
});

const models = ref<ModelDTO[]>([]);
const showInspectDialog = ref<boolean>(false);
const modelToInspect = ref<ModelDTO | null>(null);

onActivated(() => loadModelPickles());

async function loadModelPickles() {
  models.value = await api.getProjectModels(props.projectId)
  models.value.sort((a, b) => new Date(a.createdDate) < new Date(b.createdDate) ? 1 : -1);
}

async function deleteModelPickle(id: string) {
  mixpanel.track('Delete model', {id});

  let messageDTO = await api.deleteModelFiles(id);
  commitAddNotification(store, {content: messageDTO.message});
  await loadModelPickles();
}

function downloadModelPickle(id: number) {
  mixpanel.track('Download model', {id});
  api.downloadModelFile(id)
}

function cancelLaunchInspector() {
  showInspectDialog.value = false;
}

async function renameModel(id: string, name: string) {
  mixpanel.track('Update model name', {id});
  const savedDataset = await api.editModelName(id, name);
  const idx = models.value.findIndex(f => f.id === id);
  models.value[idx] = savedDataset;
  models.value = [...models.value];
}

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
