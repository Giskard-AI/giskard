<template>
	<div v-if="project" class="vertical-container">
    <v-toolbar flat dense light class="secondary--text text--lighten-2">
			<v-toolbar-title>
				<router-link to="/main/projects">
          Projects
				</router-link>
				<span class="text-subtitle-1">
          <span class="mr-1">/</span>{{ project.name }}
        </span>
			</v-toolbar-title>
      <v-spacer></v-spacer>
			<v-btn small tile color="primary" v-if="isProjectOwnerOrAdmin"
				@click="openShareDialog = true">
				<v-icon dense left>people</v-icon>
					Invite
      </v-btn>
      <v-menu left bottom offset-y rounded=0 v-if="isProjectOwnerOrAdmin">
        <template v-slot:activator="{ on, attrs }">
          <v-btn text small v-bind="attrs" v-on="on">
            <v-icon>mdi-dots-horizontal</v-icon> 
          </v-btn>
        </template>
        <v-list dense tile> 
          <v-list-item link @click="clickEditButton(); openEditDialog = true;">
						<v-list-item-title><v-icon dense left>edit</v-icon>Edit</v-list-item-title>
					</v-list-item>
          <v-list-item link @click="openDeleteDialog = true">
						<v-list-item-title class="accent--text"><v-icon dense left color="accent">delete</v-icon>Delete</v-list-item-title>
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
						<v-autocomplete
							label="Enter name or ID..."
							v-model="userToInvite"
							:items="coworkerNamesAvailable"
							:item-text="getUserFullDisplayName"
              item-value="id"
              return-object
							class="mx-2"
							outlined dense single-line hide-details
							clearable
							prepend-inner-icon="person"
							no-data-text="No user found"
						></v-autocomplete>
					</v-container>
				</v-card-text>
				<v-card-actions>
					<v-spacer></v-spacer>
					<v-btn color="secondary" text @click="openShareDialog = false">Cancel</v-btn>
					<v-btn color="primary" text @click="inviteUser()">Invite</v-btn>
				</v-card-actions>
			</v-card>
		</v-dialog>
		<!-- Edit dialog -->
		<v-dialog v-model="openEditDialog" width="500" persistent>
			<v-card>
				<v-form @submit.prevent="submitEditProject()">
					<v-card-title>Edit project details</v-card-title>
					<v-card-text>
						<ValidationProvider name="Name" mode="eager" rules="required" v-slot="{errors}">
							<v-text-field label="Project Name*" type="text" v-model="newName" :error-messages="errors"></v-text-field>
						</ValidationProvider>
						<v-text-field label="Project Description" type="text" v-model="newDescription"></v-text-field>
					</v-card-text>
					<v-card-title>Modify project settings</v-card-title>
					<v-card-text>
						<ValidationProvider name="Lime Number Samples" rules="required" v-slot="{errors}">
							<v-text-field label="Lime Number Samples*" type="number" :error-messages="errors" v-model="newLimeSamples"> </v-text-field>
						</ValidationProvider>
					</v-card-text>
					<v-card-actions>
						<v-spacer></v-spacer>
						<v-btn color="secondary" text @click="openEditDialog = false">Cancel</v-btn>
						<v-btn color="primary" text type="submit">Save</v-btn>
					</v-card-actions>
				</v-form>
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

		<v-container fluid id="container-project-tab" class="vertical-container">
			<v-tabs>
				<v-tab :to="{name: 'project-overview'}"><v-icon left>notes</v-icon>Overview</v-tab>
				<v-tab :to="{name: 'project-datasets'}"><v-icon left>stacked_bar_chart</v-icon>Datasets</v-tab>
				<v-tab :to="{name: 'project-models'}"><v-icon left>settings_suggest</v-icon>Models</v-tab>
				<v-tab :to="{name: 'project-inspector', params: tempInspectorParams}" v-if="showInspector"><v-icon left>model_training</v-icon>Inspector</v-tab>
				<v-tab :to="{name: 'project-feedbacks'}"><v-icon left small>mdi-comment-multiple-outline</v-icon>Feedback</v-tab>
				<v-tab :to="{name: 'project-test-suites'}"><v-icon left small>mdi-list-status</v-icon>Test suites</v-tab>
			</v-tabs>
      <keep-alive>
        <router-view :isProjectOwnerOrAdmin="isProjectOwnerOrAdmin"></router-view>
      </keep-alive>
		</v-container>

	</div>
</template>

<script lang="ts">
import { Component, Vue, Prop, Watch } from 'vue-property-decorator';
import { readProject, readCoworkers, readUserProfile } from '@/store/main/getters';
import { dispatchGetProject, dispatchGetCoworkers, dispatchInviteUserToProject,
	dispatchEditProject, dispatchDeleteProject } from '@/store/main/actions';
import { IUserProfileMinimal } from '@/interfaces';
import { getUserFullDisplayName } from '@/utils';
import Models from '@/views/main/project/Models.vue';
import Datasets from '@/views/main/project/Datasets.vue';
import FeedbackList from '@/views/main/project/FeedbackList.vue';
import { Role } from '@/enums';
import { ProjectPostDTO, InspectionSettings } from '@/generated-sources';
import mixpanel from "mixpanel-browser";

@Component({
	components: {
		Models, Datasets, FeedbackList
	}
})
export default class Project extends Vue {


	@Prop({ required: true }) id!: number;

	userToInvite:Partial<IUserProfileMinimal>={};
	openShareDialog = false;
	openEditDialog = false;
	openDeleteDialog = false;
	newLimeSamples = 0;
	newName = "";
	newDescription = "";

	showInspector = false;
	tempInspectorParams = {}

	public async mounted() {
		// make sure project is loaded first
		await dispatchGetProject(this.$store, {id: this.id});
    	await dispatchGetCoworkers(this.$store);

		this.setInspector(this.$router.currentRoute);
	}

	@Watch("$route", { deep: true})
	setInspector(to) {
    if (to.name === 'project-inspector') {
			this.showInspector = true
			this.tempInspectorParams = to.params
		}
	}

	get userProfile() {
		return readUserProfile(this.$store);
	}


	get coworkerNamesAvailable() {
		return readCoworkers(this.$store)
			// remove users already in guest list
			// .filter(e => !this.project?.guest_list.map(i => i.user_id).includes(e.user_id));
	}

	get project() {
		return readProject(this.$store)(this.id)
	}

	get isProjectOwnerOrAdmin() {
		return this.isUserProjectOwner || this.userProfile?.roles?.includes(Role.ADMIN)
	}

	get isUserProjectOwner() {
		return this.project && this.userProfile? this.project.owner.id == this.userProfile.id : false;
	}

	private getUserFullDisplayName = getUserFullDisplayName

	public async inviteUser() {
		if (this.project && this.userToInvite) {
			try {
        mixpanel.track('Invite user to project', {projectId: this.project.id, userId: this.userToInvite.id!});
				await dispatchInviteUserToProject(this.$store, {projectId: this.project.id, userId: this.userToInvite.id!})
				this.openShareDialog = false
			}	catch (e) {
				console.error(e)
			}
		}
	}

	public clickEditButton() {
		this.newName = this.project.name;
		this.newLimeSamples = this.project.inspectionSettings.limeNumberSamples;
		this.project.description;
	}

	public async submitEditProject() {
		if (this.project && this.newName) {
			let inspectionSettings : InspectionSettings = {
				limeNumberSamples: this.newLimeSamples
			}
			const proj: ProjectPostDTO = {
				name: this.newName,
				inspectionSettings: inspectionSettings,
				description: this.newDescription,
			}
			try {
				await dispatchEditProject(this.$store, {id: this.project.id, data: proj})
				this.openEditDialog = false;
			} catch (e) {
				console.error(e.message);
			}
		}
  }

  public async deleteProject() {
		if (this.project) {
			try {
        mixpanel.track('Delete project', {id: this.project.id});
				await dispatchDeleteProject(this.$store, {id: this.project.id})
        await this.$router.push('/main/dashboard');
			} catch (e) {
				console.error(e.message);
			}
		}
  }

}
</script>

<style scoped>
#container-project-tab {
	padding-top: 4px !important;
}
</style>
