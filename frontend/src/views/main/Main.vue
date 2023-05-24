<template>
  <v-main class="fill-height vertical-container">
    <v-navigation-drawer fixed app persistent class="background" mobile-breakpoint="sm" width="75" color="primaryLight">
      <v-layout column fill-height>
        <v-list subheader class="align-center">
          <v-list-item to="/">
            <v-list-item-content>
              <div class="align-center text-center">
                <img src="@/assets/logo_v2.png" alt="Giskard icon" width="45px" />
              </div>
            </v-list-item-content>
          </v-list-item>
          <v-divider />
          <div v-show="showProjectTabs">
            <v-list-item :to="{ name: 'project-catalog-tests' }" value="catalog-tests">
              <v-list-item-content>
                <v-icon>mdi-book-open-page-variant-outline</v-icon>
                <div class="caption">Catalog</div>
              </v-list-item-content>
            </v-list-item>
            <v-divider />
            <v-list-item :to="{ name: 'project-test-suites' }" value="test-suites">
              <v-list-item-content>
                <v-icon>mdi-list-status</v-icon>
                <div class="caption">Test</div>
              </v-list-item-content>
            </v-list-item>
            <v-divider />
            <v-list-item :to="{ name: 'project-debugger' }" value="debugger">
              <v-list-item-content>
                <v-icon>mdi-shield-search</v-icon>
                <div class="caption">Debugger</div>
              </v-list-item-content>
            </v-list-item>
            <v-divider />
            <v-list-item :to="{ name: 'project-feedbacks' }" value="feedbacks">
              <v-list-item-content>
                <v-icon>mdi-comment-multiple-outline</v-icon>
                <div class="caption">Feedback</div>
              </v-list-item-content>
            </v-list-item>
            <v-divider />
            <v-list-item :to="{ name: 'project-properties' }" value="properties">
              <v-list-item-content>
                <v-icon>mdi-file-cog-outline</v-icon>
                <div class="caption">Properties</div>
              </v-list-item-content>
            </v-list-item>
            <v-divider />
          </div>
        </v-list>
        <v-spacer></v-spacer>
        <v-list>
          <v-list-item>
            <v-list-item-content v-if="warningMessage">
              <v-tooltip right>
                <template v-slot:activator="{ on, attrs }">
                  <v-icon color="orange" v-bind="attrs" v-on="on">mdi-alert</v-icon>
                </template>
                <span>{{ warningMessage }}</span>
              </v-tooltip>
            </v-list-item-content>
          </v-list-item>
          <v-divider />
          <v-list-item to="/main/projects" exact>
            <v-list-item-content>
              <v-icon>web</v-icon>
              <div class="caption">Projects</div>
            </v-list-item-content>
          </v-list-item>
          <v-divider />
          <v-list-item v-show="hasAdminAccess" to="/main/admin/">
            <v-list-item-content>
              <v-icon>mdi-cog</v-icon>
              <div class="caption">Settings</div>
            </v-list-item-content>
          </v-list-item>
          <v-divider />
          <v-list-item to="/main/profile/view" v-if="authAvailable">
            <v-list-item-content>
              <v-icon>person</v-icon>
              <div class="caption">{{ userId }}</div>
            </v-list-item-content>
          </v-list-item>
          <v-list-item @click="logout" v-if="authAvailable">
            <v-list-item-content>
              <v-icon>logout</v-icon>
              <div class="caption">Logout</div>
            </v-list-item-content>
          </v-list-item>
        </v-list>
      </v-layout>
    </v-navigation-drawer>

    <div class="pa-0 vertical-container overflow-hidden fill-height">
        <router-view class="overflow-hidden fill-height"></router-view>
    </div>
  </v-main>
</template>

<script lang="ts" setup>
import {useUserStore} from "@/stores/user";
import {useMainStore} from "@/stores/main";
import {computed, ref} from "vue";
import {useRoute} from 'vue-router/composables';
import moment from "moment/moment";

const route = useRoute();
const mainStore = useMainStore();
const userStore = useUserStore();


let warningMessage = ref<string>()

if (mainStore.license) {
  let m = moment(String(mainStore.license.expiresOn));
  let dif = m.diff(moment(), 'days')
  if (dif <= 7) {
    warningMessage.value = `Your license expires in ${dif} days`
  }
}


const hasAdminAccess = computed(() => {

  return userStore.hasAdminAccess;
});


const authAvailable = computed(() => {
  return mainStore.authAvailable;
});

const userId = computed(() => {
  const userProfile = userStore.userProfile;
  if (userProfile) {
    return userProfile.user_id;
  } else {
    return "Guest";
  }
});

const showProjectTabs = computed(() => {
  return route.params.id !== undefined;
});

async function logout() {
  await userStore.userLogout();
}
</script>

<style scoped>
.background {
  background-image: none;
  background-position: 0 20%;
  background-size: auto 100%;
}

div.caption {
  font-size: 11px !important;
  align-self: center;
  text-align: center;
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
