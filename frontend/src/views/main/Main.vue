<template>
  <v-main class="fill-height vertical-container">
    <v-navigation-drawer fixed app permanent class='background' width='75' color='primaryLight'>
      <v-row column class="fill-height">
        <v-list subheader class='align-center' @click='resetStates'>
          <v-list-item to='/' @click.stop='() => {
            projectStore.setCurrentProjectId(null);
          }'>
            <div>
              <div class='align-center text-center'>
                <img src='@/assets/logo_v2.png' alt='Giskard icon' width='45px' />
                <span class='caption'>Projects</span>
              </div>
            </div>
          </v-list-item>
          <v-divider />

          <v-tooltip v-if="projectStore.currentProjectId === null" :disabled="projectStore.currentProjectId !== null" right>
            <template v-slot:activator="{ on, attrs }">
              <div v-on="on">
                <v-list-item :disabled="true">
                  <div>
                    <v-icon>mdi-list-status</v-icon>
                    <div class="caption">Testing</div>
                  </div>
                </v-list-item>
                <v-divider />
                <v-list-item :disabled="true">
                  <div>
                    <v-icon>mdi-book-open-page-variant-outline</v-icon>
                    <div class="caption">Catalog</div>
                  </div>
                </v-list-item>
                <v-divider />
                <v-list-item :disabled="true">
                  <div>
                    <v-icon>mdi-shield-search</v-icon>
                    <div class="caption">Debugger</div>
                  </div>
                </v-list-item>
                <v-divider />
                <v-list-item :disabled="true">
                  <div>
                    <v-icon>mdi-comment-multiple-outline</v-icon>
                    <div class="caption">Feedback</div>
                  </div>
                </v-list-item>
                <v-divider />
              </div>
            </template>
            <span>You have to select a project to interact with this menu.</span>
          </v-tooltip>

          <div v-else @click="resetStates">
            <v-list-item :to="{ name: 'project-testing', params: { id: currentProjectId } }" value="testing">
              <div>
                <v-icon>mdi-list-status</v-icon>
                <div class="caption">Testing</div>
              </div>
            </v-list-item>
            <v-divider />
            <v-list-item :to="{ name: 'project-catalog', params: { id: currentProjectId } }" value="catalog">
              <div>
                <v-icon>mdi-book-open-page-variant-outline</v-icon>
                <div class="caption">Catalog</div>
              </div>
            </v-list-item>
            <v-divider />
            <v-list-item :to="{ name: 'project-debugger', params: { id: currentProjectId } }" value="debugger">
              <div>
                <v-icon>mdi-shield-search</v-icon>
                <div class="caption">Debugger</div>
              </div>
            </v-list-item>
            <v-divider />
            <v-list-item :to="{ name: 'project-feedback', params: { id: currentProjectId } }" value="feedbacks">
              <div>
                <v-icon>mdi-comment-multiple-outline</v-icon>
                <div class="caption">Feedback</div>
              </div>
            </v-list-item>
            <v-divider />
          </div>
        </v-list>
        <v-spacer></v-spacer>
        <v-list>
          <v-list-item>
            <div v-if="warningMessage">
              <v-tooltip right>
                <template v-slot:activator="{ on, attrs }">
                  <v-icon color="orange" v-bind="attrs" v-on="on">mdi-alert</v-icon>
                </template>
                <span>{{ warningMessage }}</span>
              </v-tooltip>
            </div>
          </v-list-item>
          <v-divider />
          <v-list-item v-show="hasAdminAccess" to="/main/admin/">
            <div>
              <v-icon>mdi-cog</v-icon>
              <div class="caption">Settings</div>
            </div>
          </v-list-item>
          <v-divider />
          <v-list-item to="/main/profile/view" v-if="authAvailable">
            <div>
              <v-icon>person</v-icon>
              <div class="caption">{{ userId }}</div>
            </div>
          </v-list-item>
          <v-divider v-if="authAvailable" />
          <v-list-item @click="logout" v-if="authAvailable">
            <div>
              <v-icon>logout</v-icon>
              <div class="caption">Logout</div>
            </div>
          </v-list-item>
        </v-list>
      </v-row>
    </v-navigation-drawer>

    <div class="pa-0 vertical-container overflow-hidden fill-height">
      <router-view class="overflow-hidden fill-height"></router-view>
    </div>
  </v-main>
</template>

<script lang="ts" setup>
import { useUserStore } from '@/stores/user';
import { useMainStore } from '@/stores/main';
import { useProjectStore } from '@/stores/project';
import { useDebuggingSessionsStore } from '@/stores/debugging-sessions';
import { useTestSuitesStore } from '@/stores/test-suites';
import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import moment from 'moment/moment';
import { state, client } from '@/socket';

const route = useRoute();
const mainStore = useMainStore();
const userStore = useUserStore();
const projectStore = useProjectStore();
const debuggingSessionsStore = useDebuggingSessionsStore();
const testSuitesStore = useTestSuitesStore();

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

const currentProjectId = computed(() => {
  if (projectStore.currentProjectId === null) {
    return null;
  }
  return projectStore.currentProjectId.toString();
});

async function logout() {
  await userStore.userLogout();
}

function resetStates() {
  debuggingSessionsStore.setCurrentDebuggingSessionId(null);
  testSuitesStore.setCurrentTestSuiteId(null);
}

watch(() => route.name, async (name) => {
  if (name === 'projects-home') {
    projectStore.setCurrentProjectId(null);
  }
})

watch(() => state, () => { })

onMounted(() => {
  client.activate();
})

onUnmounted(() => {
  client.deactivate();
})
</script>

<style scoped>
.background {
  background-image: none;
  background-position: 0 20%;
  background-size: auto 100%;
}

div.caption {
  font-size: 0.6875em !important;
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
