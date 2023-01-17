<template>
  <div>
    <v-toolbar flat dense>
      <v-toolbar-title class="text-h6 font-weight-regular secondary--text text--lighten-1">Projects</v-toolbar-title>
      <v-spacer></v-spacer>
      <v-btn text small @click="loadProjects()" color="secondary">Reload
        <v-icon right>refresh</v-icon>
      </v-btn>
      <v-btn-toggle tile mandatory v-model="creatorFilter" class="mx-2">
        <v-btn>All</v-btn>
        <v-btn>Mine</v-btn>
        <v-btn>Others</v-btn>
      </v-btn-toggle>
      <v-btn tile small class="primary" v-if="isAdmin || isCreator" @click="openCreateDialog = true">
        <v-icon left>add_circle</v-icon>
        New
      </v-btn>
    </v-toolbar>

    <!-- Project list -->
    <div v-if="projects.length > 0">
      <v-card flat>
        <v-row class="px-2 py-1 caption secondary--text text--lighten-3">
          <v-col cols=2>Name</v-col>
          <v-col cols=2>Project key</v-col>
          <v-col cols=4>Description</v-col>
          <v-col cols=2>Created by</v-col>
          <v-col cols=2>Created on</v-col>
        </v-row>
      </v-card>
      <v-hover v-slot="{ hover }" v-for="p in projects" :key="p.id">
        <v-card outlined tile class="grey lighten-5 project"
                :class="[{'info': hover}]"
                :to="{name: 'project-overview', params: {id: p.id}}"
                v-show="creatorFilter === 0 || creatorFilter === 1 && p.owner.id === userProfile.id || creatorFilter === 2 && p.owner.id !== userProfile.id">
          <v-row class="pa-2">
            <v-col cols=2>
              <div class="subtitle-2 primary--text text--darken-1">{{ p.name }}</div>
            </v-col>
            <v-col cols=2>
              <div>{{ p.key }}</div>
            </v-col>
            <v-col cols=4>
              <div>{{ p.description || "-" }}</div>
            </v-col>
            <v-col cols=2>
              <div :class="{'font-weight-bold': p.owner.id === userProfile.id}">
                {{ p.owner.user_id === userProfile.user_id ? "me" : (p.owner.displayName || p.owner.user_id) }}
              </div>
            </v-col>
            <v-col cols=2>
              <div>{{ p.createdDate | date }}</div>
            </v-col>
          </v-row>
          <v-divider></v-divider>
        </v-card>
      </v-hover>
    </div>
    <v-container v-else class="font-weight-light font-italic secondary--text">
      <div v-if="isAdmin || isCreator">None created, none invited</div>
      <div v-else>You have not been invited to any projects yet</div>
    </v-container>

    <!-- Modal dialog to create new projects -->
    <v-dialog v-model="openCreateDialog" width="500" persistent>
      <v-card>
        <ValidationObserver ref="dialogForm">
          <v-form @submit.prevent="submitNewProject()">
            <v-card-title>New project details</v-card-title>
            <v-card-text>
              <ValidationProvider name="Name" mode="eager" rules="required" v-slot="{errors}">
                <v-text-field label="Project Name*" type="text" v-model="newProjectName"
                              :error-messages="errors"></v-text-field>
              </ValidationProvider>
              <ValidationProvider name="Key" mode="eager" rules="required" v-slot="{errors}">
                <v-text-field label="Project Key*" type="text" v-model="newProjectKey"
                              :error-messages="errors"></v-text-field>
              </ValidationProvider>
              <v-text-field label="Project Description" type="text" v-model="newProjectDesc"></v-text-field>
              <div v-if="projectCreateError" class="caption error--text">{{ projectCreateError }}</div>
            </v-card-text>
            <v-card-actions>
              <v-spacer></v-spacer>
              <v-btn color="secondary" text @click="clearAndCloseDialog()">Cancel</v-btn>
              <v-btn color="primary" text type="submit">Save</v-btn>
            </v-card-actions>
          </v-form>
        </ValidationObserver>
      </v-card>
    </v-dialog>

  </div>
</template>

<script setup lang="ts">
import {computed, onMounted, ref, watch} from "vue";
import {ValidationObserver} from "vee-validate";
import {Role} from "@/enums";
import {ProjectPostDTO} from "@/generated-sources";
import {toSlug} from "@/utils";
import {useRoute, useRouter} from "vue-router/composables";
import moment from "moment";
import {useUserStore} from "@/stores/user";
import {useProjectStore} from "@/stores/project";

const route = useRoute();
const router = useRouter();

const userStore = useUserStore();
const projectStore = useProjectStore();

const openCreateDialog = ref<boolean>(false); // toggle for edit or create dialog
const newProjectName = ref<string>("");
const newProjectKey = ref<string>("");
const newProjectDesc = ref<string>("");
const creatorFilter = ref<number>(0);
const projectCreateError = ref<string>("");


// template ref
const dialogForm = ref<InstanceType<typeof ValidationObserver> | null>(null);

onMounted(async () => {
  const f = route.query.f ? route.query.f[0] || '' : '';
  creatorFilter.value = parseInt(f) || 0;
  await loadProjects();
})

// computed
const userProfile = computed(() => {
  const userProfile = userStore.userProfile;
  if (userProfile == null) {
    throw Error("User is not defined.")
  }
  return userProfile;
});

const isAdmin = computed(() => {
  return userStore.hasAdminAccess;
});

const isCreator = computed(() => {
  return userProfile.value.roles?.includes(Role.AICREATOR);
});

const projects = computed(() => {
  return projectStore.projects
      .sort((a, b) => moment(b.createdDate).diff(moment(a.createdDate)));
})

// functions
async function loadProjects() {
  await projectStore.getProjects();
}

function clearAndCloseDialog() {
  dialogForm.value?.reset();
  openCreateDialog.value = false;
  newProjectName.value = '';
  newProjectKey.value = '';
  newProjectDesc.value = '';
  projectCreateError.value = '';
}

async function submitNewProject() {
  if (!newProjectName.value) {
    return;
  }

  const proj: ProjectPostDTO = {
    name: newProjectName.value.trim(),
    key: newProjectKey.value.trim(),
    description: newProjectDesc.value.trim(),
    inspectionSettings: {
      limeNumberSamples: 500
    }
  };

  try {
    await projectStore.createProject(proj);
    clearAndCloseDialog();
  } catch (e) {
    console.error(e.message);
    projectCreateError.value = e.message;
  }
}

// watchers
watch(() => newProjectName.value, (value) => {
  newProjectKey.value = toSlug(value);
})

</script>
