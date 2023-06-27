<template>
  <div v-if="project" class="vertical-container">
    <v-toolbar flat dense light class="secondary--text text--lighten-2">
      <v-toolbar-title class="mt-4">
        <router-link to="/main/projects">
          Projects
        </router-link>
        <span>/</span>
        <router-link :to="{ name: 'project-properties', params: { id } }">
          {{ project.name }} ({{ project.key }})
        </router-link>
        <span v-show="currentTab !== null">
          <span>/</span>
          {{ currentTabString }}
        </span>
      </v-toolbar-title>
      <v-spacer></v-spacer>
      <v-menu left bottom offset-y rounded=0 v-if="isProjectOwnerOrAdmin">
        <template v-slot:activator="{ on, attrs }">
          <v-btn text small tile v-bind="attrs" v-on="on" class="ml-2">
            <v-icon>mdi-dots-horizontal</v-icon>
          </v-btn>
        </template>
        <v-list dense tile>
          <v-list-item link :to="{ name: 'project-properties' }">
            <v-list-item-title>
              <v-icon dense left>mdi-tune</v-icon>
              Properties
            </v-list-item-title>
          </v-list-item>

          <v-tooltip :disabled="mainStore.authAvailable" bottom>
            <template v-slot:activator="{ on, attrs }">
              <div v-on="on">
                <v-list-item v-if="isProjectOwnerOrAdmin" @click="openShareDialog = true" :disabled="!mainStore.authAvailable" link>
                  <v-list-item-title>
                    <v-icon dense left>people</v-icon>
                    Invite
                  </v-list-item-title>
                </v-list-item>
              </div>
            </template>
            <span>Inviting users is only available in Giskard Starter or above.</span>
          </v-tooltip>
        </v-list>
      </v-menu>
    </v-toolbar>

    <!-- Share dialog -->
    <v-dialog persistent max-width="500" v-model="openShareDialog">
      <v-card>
        <v-card-title>
          Invite user to project
        </v-card-title>
        <v-card-text>
          <v-container fluid>
            <v-autocomplete label="Enter name or ID..." v-model="userToInvite" :items="coworkerNamesAvailable" :item-text="getUserFullDisplayName" item-value="id" return-object class="mx-2" outlined dense single-line hide-details clearable prepend-inner-icon="person" no-data-text="No user found"></v-autocomplete>
          </v-container>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="secondary" text @click="openShareDialog = false">Cancel</v-btn>
          <v-btn color="primary" text @click="inviteUser()">Invite</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete dialog -->
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

    <v-container fluid id="container-project-tab" class="vertical-container pb-0">
      <keep-alive>
        <router-view :isProjectOwnerOrAdmin="isProjectOwnerOrAdmin"></router-view>
      </keep-alive>
    </v-container>

  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { IUserProfileMinimal } from "@/interfaces";
import { Role } from "@/enums";
import mixpanel from "mixpanel-browser";
import { useRouter, useRoute } from "vue-router/composables";
import { useMainStore } from "@/stores/main";
import { useUserStore } from "@/stores/user";
import { useProjectArtifactsStore } from "@/stores/project-artifacts";
import { useProjectStore } from "@/stores/project";
import { getUserFullDisplayName } from "@/utils";

const router = useRouter();
const route = useRoute();

const mainStore = useMainStore();
const userStore = useUserStore();
const projectStore = useProjectStore();
const projectArtifactsStore = useProjectArtifactsStore();

interface Props {
  id: number
}

const props = defineProps<Props>();

const userToInvite = ref<Partial<IUserProfileMinimal>>({});
const openShareDialog = ref<boolean>(false);
const openDeleteDialog = ref<boolean>(false);
const currentTab = ref<string | null>(null);

const userProfile = computed(() => {
  return userStore.userProfile;
})

const currentTabString = computed(() => {
  return currentTab.value!.charAt(0).toUpperCase() + currentTab.value!.slice(1)
})


const coworkerNamesAvailable = computed(() => {
  return mainStore.coworkers
  // remove users already in guest list
  // .filter(e => !this.project?.guest_list.map(i => i.user_id).includes(e.user_id));
});

const project = computed(() => {
  return projectStore.project(props.id)
});

const isProjectOwnerOrAdmin = computed(() => {
  return isUserProjectOwner.value || userProfile.value?.roles?.includes(Role.ADMIN)
});

const isUserProjectOwner = computed(() => {
  return project.value && userProfile.value ? project.value?.owner.id == userProfile.value?.id : false;
});


async function inviteUser() {
  if (project.value && userToInvite.value) {
    try {
      mixpanel.track('Invite user to project', { projectId: project.value?.id, userId: userToInvite.value?.id! });
      await projectStore.inviteUserToProject({ projectId: project.value!.id, userId: userToInvite.value!.id! })
      openShareDialog.value = false
    } catch (e) {
      console.error(e)
    }
  }
}

function exportProject(id: number) {
  mixpanel.track('Export project', { id });
  projectStore.exportProject(id);
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

function updateCurrentTab() {
  currentTab.value = route.fullPath.split('/')[4] || null;
}


watch(() => route.fullPath, async () => {
  updateCurrentTab();
})

onMounted(async () => {
  await projectStore.getProject({ id: props.id });
  projectStore.setCurrentProjectId(props.id);
  await mainStore.getCoworkers();
  updateCurrentTab();
  await projectArtifactsStore.setProjectId(props.id, false);
})
</script>

<style scoped>
#container-project-tab {
  padding-top: 4px !important;
}
</style>
