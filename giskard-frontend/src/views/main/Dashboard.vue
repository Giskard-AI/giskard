<template>
  <div>
  <v-toolbar flat light><v-toolbar-title class="text-h5 font-weight-light">Welcome, {{greetedUser}}!</v-toolbar-title></v-toolbar>

  <v-container fluid>
    <div class="my-2 text-h6 secondary--text font-weight-light">You have...</div>
    <v-row>
      <v-col sm=4 lg=3 v-if="isAdmin || isCreator">
        <v-card dark tile color="success" :to="{path: '/main/projects', query: {f: 1}}">
          <v-card-title class="text-h2">{{ projects.filter(p => p.owner_details.id == userProfile.id).length }}
            <v-spacer></v-spacer>
            <v-icon style="font-size: 4rem">model_training</v-icon></v-card-title>
          <v-card-subtitle class="text-h5">projects</v-card-subtitle>
        </v-card>
      </v-col>
      <v-col sm=4 lg=3>
        <v-card dark tile color="secondary" :to="{path: '/main/projects', query: {f: 2}}">
          <v-card-title class="text-h2">{{ projects.filter(p => p.owner_details.id != userProfile.id).length }}
            <v-spacer></v-spacer>
            <v-icon style="font-size: 4rem">group_work</v-icon></v-card-title>
          <v-card-subtitle class="text-h5">projects invited to</v-card-subtitle>
        </v-card>
      </v-col>
      <v-col sm=4 lg=3 v-if="isAdmin">
        <v-card dark tile color="warning" to="/main/admin/users">
          <v-card-title class="text-h2">{{ users.length }}
            <v-spacer></v-spacer>
            <v-icon style="font-size: 4rem">groups</v-icon></v-card-title>
          <v-card-subtitle class="text-h5">managed users</v-card-subtitle>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
  </div>
</template>

<script lang="ts">
import { Component, Vue } from 'vue-property-decorator';
import { readUserProfile, readAllProjects, readHasAdminAccess } from '@/store/main/getters';
import { readAdminUsers } from '@/store/admin/getters';
import { dispatchGetUsers } from '@/store/admin/actions';
import { dispatchGetProjects } from '@/store/main/actions';
import { Role } from '@/enums';

@Component
export default class Dashboard extends Vue {

  public async mounted() {
    await dispatchGetProjects(this.$store);
    await dispatchGetUsers(this.$store);
  }

  get userProfile() {
    return readUserProfile(this.$store);
  }

  get isAdmin() {
    return readHasAdminAccess(this.$store);
  }

  get isCreator() {
    return this.userProfile?.roles?.includes(Role.AICREATOR)
  }

  get projects() {
    return readAllProjects(this.$store);
  }

  get users() {
    if (this.isAdmin) {
      return readAdminUsers(this.$store);
    } else return []
  }

  get greetedUser() {
    const userProfile = this.userProfile;
    if (userProfile) {
      if (userProfile.display_name) {
        return userProfile.display_name;
      } else if (userProfile.user_id) {
        return userProfile.user_id;
      } else {
        return userProfile.email;
      }
    } else return "guest"
  }


}
</script>
