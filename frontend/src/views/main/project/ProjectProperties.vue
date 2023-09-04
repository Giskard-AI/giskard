<template>
  <v-container fluid class="font-weight-light mt-3">
    <v-row>
      <v-col cols='12'>
        <v-card height='100%' outlined>
          <v-card-title class='font-weight-light secondary--text py-1 mt-2'>
            Project Settings
            <v-spacer></v-spacer>
            <v-btn text @click='exportProject(project.id)'>
              <v-icon left color='primary'>mdi-application-export</v-icon>
              Export
            </v-btn>
            <v-btn class='ml-2' color='accent' text @click='openDeleteDialog = true' v-if='isProjectOwnerOrAdmin'>
              <v-icon left>delete</v-icon>
              Delete
            </v-btn>
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
                    <td @click.stop.prevent="copyText(project.key, 'Copied project key')" class="hoverable">{{ project.key }}</td>
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
import { copyText, getUserFullDisplayName } from '@/utils';
import { IUserProfileMinimal } from '@/interfaces';
import mixpanel from 'mixpanel-browser';
import { useProjectStore } from '@/stores/project';
import { computed, ref } from 'vue';
import { $vfm } from 'vue-final-modal';
import ConfirmModal from '@/views/main/project/modals/ConfirmModal.vue';
import InlineEditText from '@/components/InlineEditText.vue';
import { ProjectPostDTO } from '@/generated-sources';
import { useRouter } from 'vue-router';

const router = useRouter();


interface Props {
  projectId: number;
  isProjectOwnerOrAdmin: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  isProjectOwnerOrAdmin: false
});


const projectStore = useProjectStore();

const openDeleteDialog = ref(false);

const project = computed(() => useProjectStore().project(props.projectId))

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

function exportProject(id: number) {
  mixpanel.track('Export project', { id });
  projectStore.exportProject(id);
}

async function renameProjectName(newName: string) {
  if (!newName) return;

  const proj: ProjectPostDTO = {
    name: newName,
    description: project.value!.description,
  }

  await editProject(proj);
}

async function renameProjectDescription(newDescription: string) {
  if (!newDescription) return;

  const proj: ProjectPostDTO = {
    name: project.value!.name,
    description: newDescription,
  }

  await editProject(proj);
}

async function editProject(data: ProjectPostDTO) {
  await projectStore.editProject({ id: project.value!.id, data })
}

async function deleteProject() {
  if (project.value) {
    mixpanel.track('Delete project', { id: project.value!.id });
    await projectStore.deleteProject({ id: project.value!.id })
    await router.push('/main/dashboard');
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

.hoverable {
  cursor: pointer;
}
</style>
