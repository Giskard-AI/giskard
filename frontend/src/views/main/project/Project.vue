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
          <v-list-item link @click="clickEditButton()">
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

<script setup lang="ts">
import {computed, onMounted, ref, watch} from "vue";
import {IUserProfileMinimal} from "@/interfaces";
import {Watch} from "vue-property-decorator";
import {Role} from "@/enums";
import mixpanel from "mixpanel-browser";
import {InspectionSettings, ProjectPostDTO} from "@/generated-sources";
import {useRoute, useRouter} from "vue-router/composables";
import {useMainStore} from "@/stores/main";
import {useUserStore} from "@/stores/user";
import {useProjectStore} from "@/stores/project";
import {Route} from "vue-router";
import {getUserFullDisplayName} from "@/utils";

const route = useRoute();
const router = useRouter();

const mainStore = useMainStore();
const userStore = useUserStore();
const projectStore = useProjectStore();

interface Props {
  id: number
}

const props = defineProps<Props>();

const userToInvite = ref<Partial<IUserProfileMinimal>>({});
const openShareDialog = ref<boolean>(false);
const openEditDialog = ref<boolean>(false);
const openDeleteDialog = ref<boolean>(false);
const newLimeSamples = ref<number>(0);
const newName = ref<string>("");
const newDescription = ref<string>("");
const showInspector = ref<boolean>(false);
const tempInspectorParams = ref<any>({}); // Type this later?

onMounted(async () => {
  // make sure project is loaded first
  await projectStore.getProject({id: props.id});
  await mainStore.getCoworkers();

  setInspector(router.currentRoute);
})

watch(() => (route), setInspector, { deep: true });

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

function setInspector(to: Route) {
  if (to.name === 'project-inspector') {
    showInspector.value = true;
    tempInspectorParams.value = to.params;
  }
}

async function inviteUser() {
  if (project.value && userToInvite.value) {
    try {
      mixpanel.track('Invite user to project', {projectId: project.value?.id, userId: userToInvite.value?.id!});
      await projectStore.inviteUserToProject({projectId: project.value!.id, userId: userToInvite.value!.id!})
      openShareDialog.value = false
    }	catch (e) {
      console.error(e)
    }
  }
}

function clickEditButton() {
  if (!project.value) {
    return;
  }
  newName.value = project.value!.name;
  newLimeSamples.value = project.value!.inspectionSettings.limeNumberSamples;
  newDescription.value = project.value!.description;
  openEditDialog.value = true;
}

async function submitEditProject() {
  if (project.value && newName.value) {
    let inspectionSettings : InspectionSettings = {
      limeNumberSamples: newLimeSamples.value
    }
    const proj: ProjectPostDTO = {
      name: newName.value,
      inspectionSettings: inspectionSettings,
      description: newDescription.value,
    }
    try {
      await projectStore.editProject({id: project.value!.id, data: proj})
      openEditDialog.value = false;
    } catch (e) {
      console.error(e.message);
    }
  }
}

async function deleteProject() {
  if (project.value) {
    try {
      mixpanel.track('Delete project', {id: project.value!.id});
      await projectStore.deleteProject({id: project.value!.id})
      await router.push('/main/dashboard');
    } catch (e) {
      console.error(e.message);
    }
  }
}
</script>

<style scoped>
#container-project-tab {
	padding-top: 4px !important;
}
</style>
