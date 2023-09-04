<template>
  <div v-if="mainStore.authAvailable">
    <v-toolbar flat light v-if="mainStore.authAvailable">
      <v-toolbar-title class="text-h5 font-weight-light">Welcome, {{ greetedUser }}!</v-toolbar-title>
    </v-toolbar>

    <v-container fluid>
      <div class="my-2 text-h6 secondary--text font-weight-light">You have...</div>
      <v-row>
        <v-col sm=4 lg=3 v-if="isAdmin || isCreator">
          <v-card dark tile color="success" :to="{path: '/main/projects', query: {f: 1}}">
            <v-card-title class="text-h2">{{ projects.filter(p => p.owner.id === userProfile.id).length }}
              <v-spacer></v-spacer>
              <v-icon style="font-size: 4rem">model_training</v-icon>
            </v-card-title>
            <v-card-subtitle class="text-h5">projects</v-card-subtitle>
          </v-card>
        </v-col>
        <v-col sm=4 lg=3>
          <v-card dark tile color="secondary" :to="{path: '/main/projects', query: {f: 2}}">
            <v-card-title class="text-h2">{{ projects.filter(p => p.owner.id !== userProfile.id).length }}
              <v-spacer></v-spacer>
              <v-icon style="font-size: 4rem">group_work</v-icon>
            </v-card-title>
            <v-card-subtitle class="text-h5">projects invited to</v-card-subtitle>
          </v-card>
        </v-col>
        <v-col sm=4 lg=3 v-if="isAdmin && mainStore.authAvailable">
          <v-card dark tile color="warning" to="/main/admin/users">
            <v-card-title class="text-h2">{{ users.length }}
              <v-spacer></v-spacer>
              <v-icon style="font-size: 4rem">groups</v-icon>
            </v-card-title>
            <v-card-subtitle class="text-h5">managed users</v-card-subtitle>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import {computed, onMounted} from "vue";
import {useProjectStore} from "@/stores/project";
import {useUserStore} from "@/stores/user";
import {useAdminStore} from "@/stores/admin";
import {Role} from "@/enums";
import {useMainStore} from "@/stores/main";
import {useRouter} from "vue-router";

const router = useRouter();
const projectStore = useProjectStore();
const mainStore = useMainStore();
const userStore = useUserStore();
const adminStore = useAdminStore();


onMounted(async () => {
  // Route guard: If auth is disabled, the dashboard makes no sense!
  if (!mainStore.authAvailable) {
    await router.push("/main/projects");
  }

  await projectStore.getProjects();
  if (userStore.hasAdminAccess) {
    await adminStore.getUsers();
  }
});

const userProfile = computed(() => {
  return userStore.userProfile;
});

const isAdmin = computed(() => {
  return userStore.hasAdminAccess;
});

const isCreator = computed(() => {
  return userProfile.value?.roles?.includes(Role.AICREATOR)
});

const projects = computed(() => {
  return projectStore.projects;
});

const users = computed(() => {
  if (isAdmin.value) {
    return adminStore.users;
  } else return []
});

const greetedUser = computed(() => {
  if (userProfile.value) {
    if (userProfile.value?.displayName) {
      return userProfile.value?.displayName;
    } else if (userProfile.value?.user_id) {
      return userProfile.value?.user_id;
    } else {
      return userProfile.value?.email;
    }
  } else return "guest"
});
</script>