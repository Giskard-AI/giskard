<template>
  <div>HOHO</div>
</template>

<!--<script setup lang="ts">-->
<!--import {computed, onMounted, ref, watch} from "vue";-->
<!--import {copyToClipboard} from "@/global-keys";-->
<!--import {TYPE} from "vue-toastification";-->
<!--import {IUserProfileMinimal} from "@/interfaces";-->
<!--import {Role} from "@/enums";-->
<!--import mixpanel from "mixpanel-browser";-->
<!--import {useRoute, useRouter} from "vue-router";-->
<!--import {useMainStore} from "@/stores/main";-->
<!--import {useUserStore} from "@/stores/user";-->
<!--import {useProjectArtifactsStore} from "@/stores/project-artifacts";-->
<!--import {useProjectStore} from "@/stores/project";-->

<!--const router = useRouter();-->
<!--const route = useRoute();-->

<!--const mainStore = useMainStore();-->
<!--const userStore = useUserStore();-->
<!--const projectStore = useProjectStore();-->
<!--const projectArtifactsStore = useProjectArtifactsStore();-->

<!--interface Props {-->
<!--  id: number-->
<!--}-->

<!--const props = defineProps<Props>();-->

<!--const userToInvite = ref<Partial<IUserProfileMinimal>>({});-->
<!--const openShareDialog = ref<boolean>(false);-->
<!--const openDeleteDialog = ref<boolean>(false);-->
<!--const currentTab = ref<string | null>(null);-->

<!--const userProfile = computed(() => {-->
<!--  return userStore.userProfile;-->
<!--})-->

<!--const currentTabString = computed(() => {-->
<!--  let tabString = currentTab.value?.split('-')[1] || '';-->
<!--  tabString = tabString.charAt(0).toUpperCase() + tabString.slice(1);-->
<!--  return tabString-->
<!--})-->


<!--const coworkerNamesAvailable = computed(() => {-->
<!--  return mainStore.coworkers-->
<!--  // remove users already in guest list-->
<!--  // .filter(e => !this.project?.guest_list.map(i => i.user_id).includes(e.user_id));-->
<!--});-->

<!--const project = computed(() => {-->
<!--  return projectStore.project(props.id)-->
<!--});-->

<!--const isProjectOwnerOrAdmin = computed(() => {-->
<!--  return isUserProjectOwner.value || userProfile.value?.roles?.includes(Role.ADMIN)-->
<!--});-->

<!--const isUserProjectOwner = computed(() => {-->
<!--  return project.value && userProfile.value ? project.value?.owner.id == userProfile.value?.id : false;-->
<!--});-->


<!--async function inviteUser() {-->
<!--  if (project.value && userToInvite.value) {-->
<!--    try {-->
<!--      mixpanel.track('Invite user to project', {projectId: project.value?.id, userId: userToInvite.value?.id!});-->
<!--      await projectStore.inviteUserToProject({projectId: project.value!.id, userId: userToInvite.value!.id!})-->
<!--      openShareDialog.value = false-->
<!--    } catch (e) {-->
<!--      console.error(e)-->
<!--    }-->
<!--  }-->
<!--}-->

<!--function exportProject(id: number) {-->
<!--  mixpanel.track('Export project', {id});-->
<!--  projectStore.exportProject(id);-->
<!--}-->

<!--async function deleteProject() {-->
<!--  if (project.value) {-->
<!--    try {-->
<!--      mixpanel.track('Delete project', {id: project.value!.id});-->
<!--      await projectStore.deleteProject({id: project.value!.id})-->
<!--      await router.push('/main/dashboard');-->
<!--    } catch (e) {-->
<!--      console.error(e.message);-->
<!--    }-->
<!--  }-->
<!--}-->

<!--function updateCurrentTab() {-->
<!--  currentTab.value = route.name?.split('-').slice(0, 2).join('-') || null;-->
<!--}-->

<!--async function copyProjectKey() {-->
<!--  await copyToClipboard(project.value!.key);-->
<!--  mainStore.addNotification({content: "Copied project key to clipboard", color: TYPE.SUCCESS});-->
<!--}-->


<!--watch(() => route.fullPath, async () => {-->
<!--  updateCurrentTab();-->
<!--})-->

<!--onMounted(async () => {-->
<!--  await projectStore.getProject({id: props.id});-->
<!--  projectStore.setCurrentProjectId(props.id);-->
<!--  await mainStore.getCoworkers();-->
<!--  updateCurrentTab();-->
<!--  await projectArtifactsStore.setProjectId(props.id, false);-->
<!--})-->
<!--</script>-->

<style scoped>
#container-project-tab {
  padding-top: 4px !important;
}

#current-route {
  font-size: 1.125rem !important;
}

#project-key {
  font-size: 0.675rem !important;
  line-height: 0.675rem !important;
}

#project-key span {
  text-decoration: underline;
  margin-right: 0.2rem;
}
</style>
