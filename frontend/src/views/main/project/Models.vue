<template>
  <div class="vertical-container">
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
                <template v-slot:activator=" { on, attrs } ">
                  <v-btn icon color="info" @click=" downloadModelPickle(m.id) " v-bind=" attrs " v-on=" on ">
                    <v-icon>download</v-icon>
                  </v-btn>
                </template>
                <span>Download</span>
              </v-tooltip>
              <DeleteModal v-if=" isProjectOwnerOrAdmin " :id=" m.id " :file-name=" m.fileName " type="model" @submit=" deleteModelPickle(m.id) " />
            </div>
          </v-col>
        </v-row>
        <v-divider></v-divider>
      </v-card>

      <!-- Dialog for launching model inspection -->
      <v-dialog persistent max-width="600" v-model=" showInspectDialog " class="inspector-launcher-container">
        <InspectorLauncher :projectId=" projectId " :model=" modelToInspect " @cancel=" cancelLaunchInspector() " />
      </v-dialog>

    </v-container>
    <v-container v-else class="font-weight-light font-italic secondary--text">
      No models uploaded yet.
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { api } from '@/api';
import InspectorLauncher from './InspectorLauncher.vue';
import { ModelDTO } from '@/generated-sources';
import mixpanel from "mixpanel-browser";
import { onBeforeMount, ref } from 'vue';
import DeleteModal from '@/views/main/project/modals/DeleteModal.vue';
import InlineEditText from '@/components/InlineEditText.vue';
import { useMainStore } from "@/stores/main";
import { useProjectArtifactsStore } from "@/stores/project-artifacts";

const projectArtifactsStore = useProjectArtifactsStore();

const props = withDefaults(defineProps<{
  projectId: number,
  isProjectOwnerOrAdmin: boolean
}>(), {
  isProjectOwnerOrAdmin: false
});

const showInspectDialog = ref<boolean>(false);
const modelToInspect = ref<ModelDTO | null>(null);


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

onBeforeMount(async () => {
  await projectArtifactsStore.setProjectId(props.projectId);
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
