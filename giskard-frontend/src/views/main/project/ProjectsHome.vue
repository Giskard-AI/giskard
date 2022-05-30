<template>
  <div>
    <v-toolbar flat dense>
      <v-toolbar-title class="text-h6 font-weight-regular secondary--text text--lighten-1">Projects</v-toolbar-title>
      <v-spacer></v-spacer>
      <v-btn text small @click="loadProjects()" color="secondary">Reload<v-icon right>refresh</v-icon></v-btn>
      <v-btn-toggle tile mandatory v-model="creatorFilter" class="mx-2">
        <v-btn>All</v-btn>
        <v-btn>Mine</v-btn>
        <v-btn>Others</v-btn>
      </v-btn-toggle>
      <v-btn tile small class="primary" v-if="isAdmin || isCreator" @click="openCreateDialog = true">
        <v-icon left>add_circle</v-icon>New
      </v-btn>
    </v-toolbar>

      <!-- Project list -->
      <v-container v-if="projects.length > 0">
        <v-card flat>
          <v-row class="px-2 py-1 caption secondary--text text--lighten-3">
            <v-col cols=3>Name</v-col>
            <v-col cols=5>Description</v-col>
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
            <v-col cols=3>
              <div class="subtitle-2 primary--text text--darken-1">{{ p.name }}</div>
            </v-col>
            <v-col cols=5>
              <div>{{ p.description || "-"}}</div>
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
      </v-container>
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
              <v-text-field label="Project Description" type="text" v-model="newProjectDesc"></v-text-field>
              <div v-if="projectCreateError" class="caption error--text">{{projectCreateError}}</div>
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

<script lang="ts">
import { Component, Vue } from 'vue-property-decorator';
import { ValidationObserver } from 'vee-validate'
import { readUserProfile, readAllProjects, readHasAdminAccess } from '@/store/main/getters';
import { Role } from '@/enums';
import { dispatchGetProjects, dispatchCreateProject } from '@/store/main/actions';
import { ProjectPostDTO } from '@/generated-sources';
import moment from "moment";

@Component
export default class ProjectsHome extends Vue {

  private openCreateDialog = false; // toggle for edit or create dialog
  private newProjectName = "";
  private newProjectDesc = "";
  private creatorFilter = 0;
  private projectCreateError = "";

  $refs!: {
    dialogForm: InstanceType<typeof ValidationObserver>;
  };

  public async mounted() {
    const f = this.$route.query.f ? this.$route.query.f[0] || "" : ""
    this.creatorFilter = parseInt(f) || 0;
    await this.loadProjects();
  }

  private async loadProjects() {
    await dispatchGetProjects(this.$store);
  }

  get userProfile() {
    return readUserProfile(this.$store);
  }

  public get isAdmin() {
    return readHasAdminAccess(this.$store); 
  }

  public get isCreator() {
    return this.userProfile?.roles?.includes(Role.AICREATOR);
  }

  get projects() {
    return readAllProjects(this.$store)
      .sort((a, b) => moment(b.createdDate).diff(moment(a.createdDate)));
  }

  public clearAndCloseDialog() {
    this.$refs.dialogForm.reset();
    this.openCreateDialog = false;
    this.newProjectName = "";
    this.newProjectDesc = "";
    this.projectCreateError = "";
  }

  public async submitNewProject() {
    if (this.newProjectName) {
      const proj: ProjectPostDTO = {
        name: this.newProjectName.trim(),
        description: this.newProjectDesc.trim(),
      }
      try {
        await dispatchCreateProject(this.$store, proj)
        this.clearAndCloseDialog();
      } catch (e) {
        console.error(e.message);
        this.projectCreateError = e.message;
      }
    }
  }

}
</script>
