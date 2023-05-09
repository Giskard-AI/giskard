<template>
  <div v-if="project" class="vertical-container">
    <v-toolbar flat dense light class="secondary--text text--lighten-2">
      <v-toolbar-title>
        <router-link :to="{ name: 'project-properties', params: { id } }">
          <v-btn block color="primary" rounded="xl" text>
            <v-icon left>mdi-file-cog-outline</v-icon>
            <span class="text-subtitle-1 project-name">
              {{ project.name }}
            </span>
          </v-btn>
        </router-link>
      </v-toolbar-title>
      <v-spacer></v-spacer>
      <v-tooltip :disabled="mainStore.authAvailable" bottom>
        <template v-slot:activator="{ on, attrs }">
          <div v-on="on">
            <v-btn small tile color="primary" v-if="isProjectOwnerOrAdmin" @click="openShareDialog = true" :disabled="!mainStore.authAvailable">
              <v-icon dense left>people</v-icon>
              Invite
            </v-btn>
          </div>
        </template>
        <span>Inviting users is only available in Giskard Starter or above.</span>
      </v-tooltip>
      <v-menu left bottom offset-y rounded=0 v-if="isProjectOwnerOrAdmin">
        <template v-slot:activator="{ on, attrs }">
          <v-btn text small tile v-bind="attrs" v-on="on" class="ml-2">
            <v-icon>mdi-dots-horizontal</v-icon>
          </v-btn>
        </template>
        <v-list dense tile>
          <v-list-item link @click="exportProject(project.id)">
            <v-list-item-title>
              <v-icon dense left color="primary">mdi-application-export</v-icon>
              Export
            </v-list-item-title>
          </v-list-item>
          <v-list-item link @click="openDeleteDialog = true">
            <v-list-item-title class="accent--text">
              <v-icon dense left color="accent">delete</v-icon>
              Delete
            </v-list-item-title>
          </v-list-item>
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

    <!-- Quick start dialog -->
    <v-dialog v-model="openQuickStart" max-width="70vw">
      <v-card flat>
        <v-card-title flat>
          Quick start guide
        </v-card-title>
        <QuickStartSteepper @close="openQuickStart = false"></QuickStartSteepper>
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
import { useRouter } from "vue-router/composables";
import { useMainStore } from "@/stores/main";
import { useUserStore } from "@/stores/user";
import { useProjectArtifactsStore } from "@/stores/project-artifacts";
import { useProjectStore } from "@/stores/project";
import { getUserFullDisplayName } from "@/utils";
import QuickStartSteepper from "@/components/QuickStartSteepper.vue";

const router = useRouter();

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
const openQuickStart = ref<boolean>(false);

const userProfile = computed(() => {
  return userStore.userProfile;
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

onMounted(async () => {
  await projectStore.getProject({ id: props.id });
  await mainStore.getCoworkers();
  await projectArtifactsStore.setProjectId(props.id, false);

  if (projectArtifactsStore.datasets.length == 0 && projectArtifactsStore.models.length == 0) {
    console.log('Datasets length', projectArtifactsStore.datasets.length);
    console.log('Models length', projectArtifactsStore.models.length);
    openQuickStart.value = true;
  }
})
</script>

<style scoped>
#container-project-tab {
  padding-top: 4px !important;
}

.project-name {
  text-transform: none;
  font-weight: 500;
}
</style>
