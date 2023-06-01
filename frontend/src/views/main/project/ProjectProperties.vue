<template>
  <v-container fluid class="font-weight-light mt-3">
    <v-row>
      <v-col cols="9">
        <v-card height="100%" outlined>
          <v-card-title class="font-weight-light secondary--text py-1 mt-2">
            Project Settings
          </v-card-title>
          <v-card-text class="container pb-0">
            <v-row>
              <v-col cols="6">
                <v-simple-table class="properties-table project-properties-table-1" dense>
                  <tr>
                    <td>Project Name:</td>
                    <td>
                      <InlineEditText :text="project.name" @save="renameProjectName">
                      </InlineEditText>
                    </td>
                  </tr>
                  <tr>
                    <td>Project Description:</td>
                    <td>
                      <InlineEditText :text="project.description" @save="renameProjectDescription">
                      </InlineEditText>
                    </td>
                  </tr>
                  <tr>
                    <td>Project Unique Key:</td>
                    <td>{{ project.key }}</td>
                  </tr>
                </v-simple-table>
              </v-col>
              <v-col cols="6">
                <v-simple-table class="properties-table project-properties-table-2" dense>
                  <tr>
                    <td>Project ID:</td>
                    <td>{{ project.id }}</td>
                  </tr>
                  <tr>
                    <td>Created by:</td>
                    <td>{{ getUserFullDisplayName(project.owner) }}</td>
                  </tr>
                  <tr>
                    <td>Created at:</td>
                    <td>{{ project.createdDate | date }}</td>
                  </tr>
                  <tr>
                    <td>ML Worker:</td>
                    <td>{{ project.mlWorkerType.toLowerCase() }}</td>
                  </tr>
                </v-simple-table>
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="12">
                <h3 class="font-weight-light secondary--text">Guest Users</h3>
                <div>
                  <table v-if="project.guests.length" class="px-2">
                    <tr v-for="p in project.guests" :key="p.user_id">
                      <td class="caption pr-4">{{ getUserFullDisplayName(p) }}</td>
                      <td v-if="isProjectOwnerOrAdmin">
                        <v-btn icon small color="accent" @click="cancelUserInvitation(p)">
                          <v-icon small>person_remove</v-icon>
                        </v-btn>
                      </td>
                    </tr>
                  </table>
                  <p v-else class="caption">None</p>
                </div>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="3">
        <v-card height="100%" outlined>
          <v-card-title class="font-weight-light secondary--text">
            Explanation Properties
          </v-card-title>
          <v-card-text>
            <v-simple-table class="properties-table">
              <tr>
                <td>LIME Number Samples:</td>
                <td>
                  <InlineEditText :text="project.inspectionSettings.limeNumberSamples.toString()" editText="Change" @save="renameLimeNumberSamples" :canEdit="true">
                  </InlineEditText>
                </td>
              </tr>
            </v-simple-table>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <div class="pt-8 pb-4 d-flex">
      <div class="d-flex justify-end align-center flex-grow-1">
        <v-btn @click="reloadDataObjects()" class="pa-2 text--secondary">
          Reload
          <v-icon right>refresh</v-icon>
        </v-btn>
        <v-btn color="primary" class="mx-2" href="https://docs.giskard.ai/start/guides/upload-your-model" target="_blank">
          Upload with API
          <v-icon right>mdi-application-braces-outline</v-icon>
        </v-btn>
      </div>
    </div>

    <v-row class="mb-8">
      <v-col cols="12">
        <v-card height="100%" outlined>
          <v-card-title class="justify-space-between">
            <h3 class="flex-1 font-weight-light secondary--text">Giskard Objects</h3>
            <v-btn-toggle v-model="toggleObject" borderless mandatory color="primary">
              <v-btn value="datasets" class="py-5 px-4">
                <span>Datasets</span>
                <v-icon end class="pb-1 pl-1" :color="toggleObject === 'datasets' ? 'primary' : ''">
                  stacked_bar_chart
                </v-icon>
              </v-btn>
              <v-btn value="models" class="py-5 px-4">
                <span>Models</span>
                <v-icon end class="pb-1 pl-1" :color="toggleObject === 'models' ? 'primary' : ''">
                  settings_suggest
                </v-icon>
              </v-btn>
            </v-btn-toggle>
            <div class="flex-1"></div>
          </v-card-title>
          <v-card-text>
            <Datasets v-show="toggleObject === 'datasets'" ref="datasetsComponentRef" :projectId="projectId" :isProjectOwnerOrAdmin="isProjectOwnerOrAdmin"></Datasets>
            <Models v-show="toggleObject === 'models'" ref="modelsComponentRef" :projectId="projectId" :isProjectOwnerOrAdmin="isProjectOwnerOrAdmin"></Models>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-dialog persistent max-width="340" v-model="openDeleteDialog">
      <v-card>
        <v-card-title>
          Are you sure you want to delete project?
        </v-card-title>
        <v-card-text class="accent--text">
          All data and files will be lost!
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="secondary" text @click="openDeleteDialog = false">Cancel</v-btn>
          <v-btn color="accent" text @click="deleteProject();">Ok</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { getUserFullDisplayName } from '@/utils';
import Models from '@/views/main/project/Models.vue';
import Datasets from '@/views/main/project/Datasets.vue';
import { IUserProfileMinimal } from '@/interfaces';
import mixpanel from "mixpanel-browser";
import { useProjectStore } from "@/stores/project";
import { computed, ref } from 'vue';
import { $vfm } from 'vue-final-modal';
import ConfirmModal from '@/views/main/project/modals/ConfirmModal.vue';
import InlineEditText from '@/components/InlineEditText.vue';
import { ProjectPostDTO } from '@/generated-sources';
import { useRouter } from "vue-router/composables";



interface Props {
  projectId: number;
  isProjectOwnerOrAdmin: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  isProjectOwnerOrAdmin: false
});

const router = useRouter();

const projectStore = useProjectStore();

const openDeleteDialog = ref(false);
const datasetsComponentRef = ref<any>(null);
const modelsComponentRef = ref<any>(null);
const toggleObject = ref<string>("datasets");

const project = computed(() => useProjectStore().project(props.projectId))

function reloadDataObjects() {
  datasetsComponentRef.value.loadDatasets();
  modelsComponentRef.value.loadModelPickles();
}

async function cancelUserInvitation(user: IUserProfileMinimal) {
  $vfm.show({
    component: ConfirmModal,
    bind: {
      title: 'Cancel user invitation',
      text: `Are you sure you want to cancel invitation of user <strong>${user.user_id}</strong>?`,
    },
    on: {
      async confirm(close) {
        if (project) {
          try {
            mixpanel.track('Cancel user invitation to project', { projectId: project.id, userId: user.id });
            await useProjectStore().uninviteUserFromProject({ projectId: project.id, userId: user.id })
            close();
          } catch (e) {
            console.error(e)
          }
        }
      }
    }
  });
}

async function renameProjectName(newName: string) {
  if (!newName) return;

  const proj: ProjectPostDTO = {
    name: newName,
    description: project.value!.description,
    inspectionSettings: project.value!.inspectionSettings
  }

  await editProject(proj);
}

async function renameProjectDescription(newDescription: string) {
  if (!newDescription) return;

  const proj: ProjectPostDTO = {
    name: project.value!.name,
    description: newDescription,
    inspectionSettings: project.value!.inspectionSettings
  }

  await editProject(proj);
}

async function renameLimeNumberSamples(newLimeSamples: string) {
  const newLimeSamplesParsed = parseInt(newLimeSamples);
  if (isNaN(newLimeSamplesParsed)) return;

  const proj: ProjectPostDTO = {
    name: project.value!.name,
    description: project.value!.description,
    inspectionSettings: {
      limeNumberSamples: newLimeSamplesParsed
    }
  }

  await editProject(proj);
}

async function editProject(data: ProjectPostDTO) {
  try {
    await projectStore.editProject({ id: project.value!.id, data })
  } catch (e) {
    console.error(e.message);
  }
}

function exportProject() {
  mixpanel.track('Export project', { project: project.value!.id });
  projectStore.exportProject(project.value!.id);
}

async function deleteProject() {
  if (project.value) {
    try {
      mixpanel.track('Delete project', { id: project.value!.id });
      await projectStore.deleteProject({ id: project.value!.id })
      await router.push('/main/dashboard');
    } catch (e) {
      console.error(e.message);
    }
  }
}
</script>

<style scoped lang="scss">
.properties-table {
  tr {
    td:nth-child(2) {
      font-weight: bold;
    }
  }
}

.project-properties-table-1 {
  tr {
    td:first-child {
      width: 150px;
    }
  }
}

.project-properties-table-2 {
  tr {
    td:first-child {
      width: 100px;
    }
  }
}

.flex-1 {
  flex: 1;
}
</style>
