<template>
  <v-main>
    <v-navigation-drawer
      dark
      fixed
      app
      persistent
      class="background"
      mobile-breakpoint="sm"
      width="72"
    >
      <v-layout column fill-height>
        <v-list subheader align="center">
          <v-list-item to="/">
            <v-list-item-content>
              <div>
                <img src="@/assets/favicon.png" width="46px" alt="Giskard icon"/>
              </div>
            </v-list-item-content>
          </v-list-item>
          <v-divider></v-divider>
          <v-list-item to="/main/projects">
            <v-list-item-content>
              <v-icon>web</v-icon>
              <div class="caption">Projects</div>
            </v-list-item-content>
          </v-list-item>
        </v-list>
        <v-spacer></v-spacer>
        <v-list align="center">
          <v-divider></v-divider>
          <v-list-item v-show="hasAdminAccess" to="/main/admin/">
            <v-list-item-content>
              <v-icon>mdi-account-group</v-icon>
              <div class="caption">Admin</div>
            </v-list-item-content>
          </v-list-item>
          <v-divider></v-divider>
          <v-list-item to="/main/profile/view">
            <v-list-item-content>
              <v-icon>person</v-icon>
              <div class="caption">{{ userId }}</div>
            </v-list-item-content>
          </v-list-item>
          <v-list-item @click="logout">
            <v-list-item-content>
              <v-icon>logout</v-icon>
              <div class="caption">Logout</div>
            </v-list-item-content>
          </v-list-item>
        </v-list>
      </v-layout>
    </v-navigation-drawer>

    <v-main class="pa-1">
      <router-view></router-view>
    </v-main>
  </v-main>
</template>

<script lang="ts">
import { Vue, Component } from "vue-property-decorator";

import { appName } from "@/env";
import { readHasAdminAccess } from "@/store/main/getters";
import { readUserProfile } from "@/store/main/getters";
import { dispatchUserLogOut } from "@/store/main/actions";

const routeGuardMain = async (to, from, next) => {
  if (to.path === "/main") {
    next("/main/dashboard");
  } else {
    next();
  }
};

@Component
export default class Main extends Vue {
  public appName = appName;
  private miniDrawer = false;

  public beforeRouteEnter(to, from, next) {
    routeGuardMain(to, from, next);
  }

  public beforeRouteUpdate(to, from, next) {
    routeGuardMain(to, from, next);
  }

  public get hasAdminAccess() {
    return readHasAdminAccess(this.$store);
  }

  get userId() {
    const userProfile = readUserProfile(this.$store);
    if (userProfile) {
      return userProfile.user_id;
    } else {
      return "Guest";
    }
  }

  public async logout() {
    await dispatchUserLogOut(this.$store);
  }
}
</script>

<style scoped>
.background {
  background-image: url("~@/assets/wallpaper-skyline-reduced.jpg");
  background-position: 0 20%;
  background-size: auto 100%;
}

div.caption {
  font-size: 11px !important;
  align-self: center;
}
.v-list-item {
  padding: 0 10px;
}
</style>
<style>
header.v-toolbar a {
  text-decoration: none;
}
</style>
