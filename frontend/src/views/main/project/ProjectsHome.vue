<template>
  <div>
    <v-toolbar flat>
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
      <v-menu>
        <template v-slot:activator="{ on, attrs }">
          <v-btn
            small
            color="primary"
            dark
            v-bind="attrs"
            v-on="on"
          >
            Add Project
          </v-btn>
        </template>
        <v-list>
          <v-list-item-group>
            <v-list-item @click="openCreateDialog=true">
              <v-list-item-content>
               New
              </v-list-item-content>
            </v-list-item>
            <v-list-item @click="openImportDialog=true">
              <v-list-item-content>
               Import
              </v-list-item-content>
            </v-list-item>
          </v-list-item-group>
        </v-list>
      </v-menu>
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
    

    <!-- Modal dialog to import new projects -->
    <v-dialog v-model="openImportDialog" width="500" persistent>
      <v-card>
        <ValidationObserver ref="dialogForm">
          <v-form @submit.prevent="importProject()">
            <v-card-title>Import project</v-card-title>
            <v-card-text>
              <ValidationProvider name="File" rules="required" v-slot="{errors}">
                  <v-file-input ref="file" accept=".zip" label="Select a project to import*"
                  :error-messages="errors"
                ></v-file-input>
              </ValidationProvider>
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

    <!-- Modal dialog to set the project key in case of conflict key while importing -->
    <v-dialog v-model="openConflictImportDialog" width="500" persistent>
      <v-card>
        <ValidationObserver ref="dialogForm">
          <v-form @submit.prevent="importConflictedProject()">
            <v-card-title>Set new key for the imported project</v-card-title>
            <v-card-text>
              <ValidationProvider ref="validatorNewKey" name="Name" mode="eager" rules="required" v-slot="{errors}">
                <v-text-field label="Project Key*" type="text" v-model="newProjectKey"
                              :error-messages="errors"></v-text-field>
              </ValidationProvider>
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
import {dispatchCreateProject, dispatchGetProjects} from "@/store/main/actions";
import {readAllProjects, readHasAdminAccess, readUserProfile} from "@/store/main/getters";
import {Role} from "@/enums";
import {ProjectPostDTO} from "@/generated-sources";
import {toSlug} from "@/utils";
import store from "@/store";
import {useRoute} from "vue-router/composables";
import moment from "moment";
import { api } from "@/api";

const route = useRoute();

const openCreateDialog = ref<boolean>(false); // toggle for edit or create dialog
const openImportDialog = ref<boolean>(false);
const openConflictImportDialog = ref<boolean>(false);
const newProjectName = ref<string>("");
const newProjectKey = ref<string>("");
const newProjectDesc = ref<string>("");
const creatorFilter = ref<number>(0);
const projectCreateError = ref<string>("");
const pathToTmpDirectory = ref<string>("");
const validatorNewKey = ref();

// template ref
const dialogForm = ref<InstanceType<typeof ValidationObserver> | null>(null);
const file = ref<string>('');

onMounted(async () => {
  const f = route.query.f ? route.query.f[0] || '' : '';
  creatorFilter.value = parseInt(f) || 0;
  await loadProjects();
})

// computed
const userProfile = computed(() => {
  const userProfile = readUserProfile(store);
  if (userProfile == null) {
    throw Error("User is not defined.")
  }
  return userProfile;
});

const isAdmin = computed(() => {
  return readHasAdminAccess(store);
});

const isCreator = computed(() => {
  return userProfile.value.roles?.includes(Role.AICREATOR);
});

const projects = computed(() => {
  return readAllProjects(store)
      .sort((a, b) => moment(b.createdDate).diff(moment(a.createdDate)));
})

// functions
async function loadProjects() {
  await dispatchGetProjects(store);
}

async function importConflictedProject(){
  if (!newProjectKey.value) {
    return;
  }
  api.importConflictedProject(newProjectKey.value, pathToTmpDirectory.value).then(response =>{
    if (response.conflict){
      openConflictImportDialog.value = true;
      validatorNewKey.value.applyResult({
      errors: ["A project with this key already exist, please change key"],
      valid: false,
      failedRules: {} 
    });
    }
    else {
      clearAndCloseDialog();
      loadProjects(); 
      // TODO GO TO THE GOOD PROJECT
    }
  })

}

async function importProject(){
  let uploadedFile = file.value.$refs.input.files[0];
  let formData = new FormData();
  formData.append('file', uploadedFile);
  api.importProject(formData).then(response => {
    if (response.conflict){
      openConflictImportDialog.value = true;
      pathToTmpDirectory.value = response.pathImportTmp;
    }
    else {
      clearAndCloseDialog();
      loadProjects(); 
      // TODO GO TO THE GOOD PROJECT
    }
  });
}

function clearAndCloseDialog() {
  dialogForm.value?.reset();
  openCreateDialog.value = false;
  openImportDialog.value = false;
  openConflictImportDialog.value = false;
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
    await dispatchCreateProject(store, proj);
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

<style>
#create .v-speed-dial {
  position: absolute;
}

#create .v-btn--floating {
  position: relative;
}
</style>