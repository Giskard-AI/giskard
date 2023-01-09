<template>
  <v-container>
    <v-row v-if="appSettings">
      <v-col cols="6">
        <v-card height="100%">
          <v-card-title class="font-weight-light secondary--text">
            Application
          </v-card-title>
          <v-card-text>
            <v-simple-table>
              <table class="w100">
                <tr>
                  <td>Instance</td>
                  <td>{{ appSettings.generalSettings.instanceId }}</td>
                </tr>
                <tr>
                  <td>Version</td>
                  <td>{{ appSettings.version }}</td>
                </tr>
                <tr>
                  <td>Plan</td>
                  <td>{{ appSettings.planName }}</td>
                </tr>
                <tr>
                  <td colspan="2">
                    <v-divider class="divider"/>
                  </td>
                </tr>
                <tr>
                  <td>Last commit</td>
                  <td>{{ appSettings.buildCommitId }}</td>
                </tr>
                <tr>
                  <td>Last commit date</td>
                  <td>{{ appSettings.buildCommitTime | date }}</td>
                </tr>
                <tr>
                  <td>Build branch</td>
                  <td>{{ appSettings.buildBranch }}</td>
                </tr>
              </table>
            </v-simple-table>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col>
        <v-card height="100%">
          <v-card-title class="font-weight-light secondary--text">
            <span>Usage reporting</span>
            <v-spacer/>
            <v-switch
                v-model="appSettings.generalSettings.isAnalyticsEnabled"
                @change="saveGeneralSettings(appSettings.generalSettings)"
            ></v-switch>
          </v-card-title>
          <v-card-text>
            <div class="mb-2">
              <p>Giskard can send usage reports.</p>
              <p>The raw user data is never sent, only metadata. This information helps us improve the product and fix
                bugs sooner. 🐞</p>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <v-card height="100%">
          <v-card-title class="font-weight-light secondary--text d-flex">
            <span>ML Worker</span>
            <v-spacer/>
            <v-tabs class="worker-tabs">
              <v-tab @change="externalWorkerSelected=true" :disabled="mlWorkerSettingsLoading" class="worker-tab">
                <span>external</span>
                <v-icon v-show="!mlWorkerSettingsLoading" size="10"
                        :color="isWorkerAvailable(false) ? 'green': 'red'">mdi-circle
                </v-icon>
                <v-progress-circular size="20" indeterminate v-show="mlWorkerSettingsLoading"/>
              </v-tab>
              <v-tab @change="externalWorkerSelected=false" :disabled="mlWorkerSettingsLoading" class="worker-tab">
                <span>internal</span>
                <v-icon v-show="!mlWorkerSettingsLoading" size="10" :color="isWorkerAvailable(true) ? 'green': 'red'">
                  mdi-circle
                </v-icon>
                <v-progress-circular size="20" indeterminate v-show="mlWorkerSettingsLoading"/>
              </v-tab>
            </v-tabs>
            <v-btn icon @click="initMLWorkerInfo">
              <v-icon>refresh</v-icon>
            </v-btn>
          </v-card-title>
          <v-card-text>
            <v-alert
                v-show="!externalWorkerSelected"
                color="primary"
                border="left"
                outlined
                colored-border
                icon="warning"
            >Internal ML Worker is only used in demo projects. For other projects use an <span
                class="font-weight-bold">External ML Worker</span>.
            </v-alert>
            <v-simple-table v-if="currentWorker">
              <table class="w100">
                <tr>
                  <th style="width: 30%"></th>
                </tr>
                <tr>
                  <td>Python version</td>
                  <td class="text-h6">{{ currentWorker.interpreterVersion }}</td>
                </tr>
                <tr>
                  <td>Python path</td>
                  <td>{{ currentWorker.interpreter }}</td>
                <tr>
                <tr>
                  <td>Giskard client version</td>
                  <td>{{ currentWorker.giskardClientVersion }}</td>
                <tr>
                  <td>Host</td>
                  <td>{{ currentWorker.platform.node }}</td>
                </tr>
                <tr>
                  <td>Process id</td>
                  <td>{{ currentWorker.pid }}</td>
                </tr>
                <tr>
                  <td>Process start time</td>
                  <td>{{ epochToDate(currentWorker.processStartTime) }}</td>
                </tr>
                <tr>
                  <td>Internal ML Worker port</td>
                  <td>{{ currentWorker.internalGrpcPort }}</td>
                </tr>
                <tr>
                  <td>Architecture</td>
                  <td>{{ currentWorker.platform.machine }}</td>
                </tr>
                <tr>
                  <td>Installed packages</td>
                  <td class="overflow-hidden">
                    <v-text-field
                        class="pt-5"
                        dense
                        v-model="installedPackagesSearch"
                        append-icon="mdi-magnify"
                        label="Search"
                        single-line
                        hide-details
                        clearable
                    ></v-text-field>
                    <v-data-table
                        dense
                        :sort-by="['name']"
                        :headers="installedPackagesHeaders"
                        :items="installedPackagesData"
                        :search="installedPackagesSearch"
                    ></v-data-table>
                  </td>
                </tr>
              </table>
            </v-simple-table>
            <v-card-text v-else class="pa-0">
              <span v-show="mlWorkerSettingsLoading">Loading information</span>
              <v-container v-show="!mlWorkerSettingsLoading" class="pa-0">
                <div v-show="!externalWorkerSelected">
                  <p>Not available. Check that internal ML Worker is running or start it with</p>
                  <p><code class="text-body-1">docker-compose up -d ml-worker</code></p>
                </div>
                <div v-show="externalWorkerSelected">
                  <v-alert
                      color="warning"
                      border="left"
                      outlined
                      colored-border
                      icon="info"
                  >No external ML Worker is connected
                  </v-alert>
                  <p>To connect a worker, install giskard library in any code environment of your choice with</p>
                  <p><code class="text-body-1">pip install giskard</code></p>
                  <p>then run</p>
                  <code class="text-body-1">
                    giskard worker start -h
                    <v-tooltip right>
                      <template v-slot:activator="{ on, attrs }">
                          <span v-bind="attrs"
                                v-on="on" class="giskard-address">{{ giskardAddress }}</span>
                      </template>
                      <p>IP address, hostname or DNS name of Giskard server can be used.</p>
                      <p>Make sure that port {{ appSettings.externalMlWorkerEntrypointPort }} is accessible</p>
                    </v-tooltip>
                    <span
                        v-if="appSettings.externalMlWorkerEntrypointPort !== 40051"> -p {{
                        appSettings.externalMlWorkerEntrypointPort
                      }}</span>
                  </code>
                  <v-btn class="ml-1" x-small icon @click="copyMLWorkerCommand">
                    <v-icon>mdi-content-copy</v-icon>
                  </v-btn>
                  <p class="mt-4 mb-0">to connect to Giskard</p>
                </div>
              </v-container>
            </v-card-text>


          </v-card-text>

        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import {computed, onBeforeMount, ref, watch} from "vue";
import {AppConfigDTO, GeneralSettings, MLWorkerInfoDTO} from "@/generated-sources";
import mixpanel from "mixpanel-browser";
import {api} from "@/api";
import moment from "moment/moment";
import {copyToClipboard} from "@/global-keys";
import {useMainStore} from "@/stores/main";
import AppInfoDTO = AppConfigDTO.AppInfoDTO;

const mainStore = useMainStore();


const appSettings = ref<AppInfoDTO | null>(null);
const currentWorker = ref<MLWorkerInfoDTO | null>(null);
const allMLWorkerSettings = ref<MLWorkerInfoDTO[]>([]);
const externalWorkerSelected = ref<boolean>(true);
const mlWorkerSettingsLoading = ref<boolean>(false);
const installedPackagesData = ref<{ name: string, version: string }[]>([]);
const giskardAddress = computed(() => window.location.hostname);
const installedPackagesSearch = ref<string>("");

const installedPackagesHeaders = [{text: 'Name', value: 'name', width: '70%'}, {
  text: 'Version',
  value: 'version',
  width: '30%'
}];

onBeforeMount(async () => {
  // TODO: Vue 2 does not support top level await in <script setup>, this can be moved when we migrate to Vue 3
  appSettings.value = mainStore.appSettings;
  await initMLWorkerInfo();
})

// TODO: Check if the array is deeply watched
watch(() => [externalWorkerSelected.value, allMLWorkerSettings.value], () => {
  if (allMLWorkerSettings.value.length) {
    currentWorker.value = allMLWorkerSettings.value.find(value => value.isRemote === externalWorkerSelected.value) || null;
    installedPackagesData.value = currentWorker.value !== null ?
        Object.entries(currentWorker.value!.installedPackages).map(([key, value]) => ({
          name: key,
          version: value
        })) : [];
  }
})

function isWorkerAvailable(isInternal: boolean): boolean {
  return allMLWorkerSettings.value.find(value => value.isRemote === !isInternal) !== undefined;
}

async function saveGeneralSettings(settings: GeneralSettings) {
  if (!settings.isAnalyticsEnabled) {
    mixpanel.opt_out_tracking();
  } else {
    mixpanel.opt_in_tracking();
  }
  appSettings.value!.generalSettings = await api.saveGeneralSettings(settings);
}

async function initMLWorkerInfo() {
  try {
    currentWorker.value = null;
    mlWorkerSettingsLoading.value = true;
    allMLWorkerSettings.value = await api.getMLWorkerSettings();
    currentWorker.value = allMLWorkerSettings.value.find(value => value.isRemote === externalWorkerSelected.value) || null;
  } catch (error) {
  } finally {
    mlWorkerSettingsLoading.value = false;
  }
}

async function copyMLWorkerCommand() {
  await copyToClipboard('giskard worker start -h ' + giskardAddress);
  mainStore.addNotification({content: 'Copied', color: '#262a2d'});
}

function epochToDate(epoch: number) {
  return moment.unix(epoch).format('DD/MM/YYYY HH:mm:ss');
}
</script>

<style lang="scss" scoped>
.worker-tab {
  display: flex;
  justify-content: space-between;
  width: 120px;
}

.giskard-address {
  border: 1px lightgrey dashed;
  padding: 2px;
}

.worker-tabs {
  width: auto;
  flex-grow: 0;
}
</style>