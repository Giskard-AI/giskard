<template>
  <div class="fill-height d-flex flex-column">
    <v-toolbar flat dense light class="flex-grow-0">
      <v-toolbar-title class="text-h6 font-weight-regular secondary--text text--lighten-1">
        My Profile
      </v-toolbar-title>
    </v-toolbar>
    <v-container class="flex-grow-1 overflow-y-auto" fluid>
      <v-row v-if="userProfile">
        <v-col>
          <v-card height="100%">
            <ValidationObserver ref="observer" v-slot="{ invalid, pristine }">
              <v-form @submit.prevent="">
                <v-card-title class="font-weight-light secondary--text">User details</v-card-title>
                <v-card-text>
                  <v-row>
                    <v-col cols=6>
                      <div>
                        <div class="caption secondary--text text--lighten-3">User ID</div>
                        <div class="subtitle-1">{{ userProfile.user_id }}</div>
                      </div>
                      <div class="mt-3">
                        <div class="caption secondary--text text--lighten-3">Display Name</div>
                        <div v-if="!editModeToggle">
                          <div class="subtitle-1" v-if="userProfile.displayName">{{ userProfile.displayName }}</div>
                          <div class="subtitle-1" v-else>(not set)</div>
                        </div>
                        <div v-else>
                          <ValidationProvider name="Display name" mode="eager" rules="min:4" v-slot="{errors}">
                            <v-text-field v-model="displayName" single-line :error-messages="errors"
                                          class="my-0 py-0"></v-text-field>
                          </ValidationProvider>
                        </div>
                      </div>
                    </v-col>
                    <v-col cols=6>
                      <div>
                        <div class="caption secondary--text text--lighten-3">Roles</div>
                        <div class="subtitle-1" v-for='role in userProfile.roles'>{{ role | roleName }}</div>
                      </div>
                      <div class="mt-3">
                        <div class="caption secondary--text text--lighten-3">Email</div>
                        <div v-if="!editModeToggle" class="subtitle-1">{{ userProfile.email }}</div>
                        <div v-else>
                          <ValidationProvider name="Email" mode="eager" rules="required|email" v-slot="{errors}">
                            <v-text-field type="email" v-model="email" single-line hide :error-messages="errors"
                                          class="my-0 py-0"></v-text-field>
                          </ValidationProvider>
                        </div>
                      </div>
                    </v-col>
                  </v-row>
                </v-card-text>
                <v-card-actions class="px-4 pb-4">
                  <v-btn tile small color="accent" to="/main/profile/password">Change password</v-btn>
                  <v-spacer></v-spacer>
                  <v-btn tile small class="primary" v-show="!editModeToggle" @click="editModeToggle = true">Edit
                  </v-btn>
                  <v-btn tile small class="secondary" v-show="editModeToggle"
                         @click="editModeToggle = false; resetFormData();">Cancel
                  </v-btn>
                  <ButtonModalConfirmation
                      v-if="editModeToggle"
                      :disabledButton="invalid || pristine"
                      @ok="submit">
                  </ButtonModalConfirmation>
                </v-card-actions>
              </v-form>
            </ValidationObserver>
          </v-card>
        </v-col>
        <v-col>
          <v-card height="100%">
            <v-card-title class="font-weight-light secondary--text">API Access Token</v-card-title>
            <v-card-text>
              <div class="mb-2">
                <v-btn small tile color="primary" @click="generateToken">Generate</v-btn>
                <v-btn v-if="apiAccessToken && apiAccessToken.id_token" small tile color="secondary" class="ml-2"
                       @click="copyToken">
                  Copy
                  <v-icon right dark>mdi-content-copy</v-icon>
                </v-btn>
              </div>
              <v-row>
                <v-col>
                  <div class="token-area-wrapper" v-if="apiAccessToken && apiAccessToken.id_token">
                    <span class="token-area" ref="apiAccessToken">{{ apiAccessToken.id_token }}</span>
                  </div>
                </v-col>
              </v-row>
              <v-row v-if="apiAccessToken && apiAccessToken.id_token">
                <v-col class="text-right">
                  Expires on <span>{{ apiAccessToken.expiryDate | date }}</span>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
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
          <v-card height="100%" v-if="isAdmin">
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
          <v-skeleton-loader v-else type="card"></v-skeleton-loader>
        </v-col>
      </v-row>
      <v-row>
        <v-col>
          <v-card height="100%" v-if="isAdmin">
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
          <v-skeleton-loader v-else type="card"></v-skeleton-loader>
        </v-col>
      </v-row>
      <v-row v-if="isAdmin">
        <v-col>
          <RunningWorkerJobs/>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script lang="ts">
import {Component, Vue, Watch} from 'vue-property-decorator';
import {readAppSettings, readUserProfile} from '@/store/main/getters';
import {api} from '@/api';
import {commitAddNotification, commitRemoveNotification} from '@/store/main/mutations';
import {dispatchUpdateUserProfile} from '@/store/main/actions';
import ButtonModalConfirmation from '@/components/ButtonModalConfirmation.vue';
import {copyToClipboard} from '@/global-keys';
import {AppConfigDTO, GeneralSettings, JWTToken, MLWorkerInfoDTO, UpdateMeDTO} from "@/generated-sources";
import mixpanel from "mixpanel-browser";
import {Role} from "@/enums";
import moment from "moment";
import store from "@/store";
import RunningWorkerJobs from '@/views/main/profile/RunningWorkerJobs.vue';
import AppInfoDTO = AppConfigDTO.AppInfoDTO;

@Component({
  components: {
    RunningWorkerJobs,
    ButtonModalConfirmation,
  },
})
export default class UserProfile extends Vue {

  private displayName: string = '';
  private email: string = '';
  private editModeToggle = false;
  private apiAccessToken: JWTToken | null = null;
  private appSettings: AppInfoDTO | null = null;
  private isAdmin: boolean = false;
  private currentWorker: MLWorkerInfoDTO | null = null;
  private allMLWorkerSettings: MLWorkerInfoDTO[] = [];
  private externalWorkerSelected = true;
  private mlWorkerSettingsLoading = false;
  private installedPackagesHeaders = [{text: 'Name', value: 'name', width: '70%'}, {
    text: 'Version',
    value: 'version',
    width: '30%'
  }];
  private installedPackagesData: { name: string, version: string }[] = [];
  private installedPackagesSearch = "";

  private resetFormData() {
    const userProfile = readUserProfile(this.$store);
    if (userProfile) {
      if (userProfile.displayName) {
        this.displayName = userProfile.displayName;
      }
      this.email = userProfile.email;
      this.isAdmin = userProfile.roles!.includes(Role.ADMIN);
    }
  }

  public async created() {
    this.appSettings = await readAppSettings(this.$store);
    await this.initMLWorkerInfo();
    this.resetFormData();
  }

  private isWorkerAvailable(isInternal: boolean): boolean {
    return this.allMLWorkerSettings.find(value => value.isRemote === !isInternal) !== undefined;
  }

  private async initMLWorkerInfo() {
    try {
      this.currentWorker = null;
      this.mlWorkerSettingsLoading = true;
      this.allMLWorkerSettings = await api.getMLWorkerSettings();
      this.currentWorker = this.allMLWorkerSettings.find(value => value.isRemote === this.externalWorkerSelected) || null;
    } catch (error) {
    } finally {
      this.mlWorkerSettingsLoading = false;
    }
  }

  public async copyMLWorkerCommand() {
    await copyToClipboard('giskard worker start -h ' + this.giskardAddress);
    commitAddNotification(store, {content: 'Copied', color: '#262a2d'});
  }

  @Watch("externalWorkerSelected")
  @Watch("allMLWorkerSettings", {deep: true})
  public mlWorkerSelected() {
    if (this.allMLWorkerSettings.length) {
      this.currentWorker = this.allMLWorkerSettings.find(value => value.isRemote === this.externalWorkerSelected) || null;
      this.installedPackagesData = this.currentWorker !== null ?
          Object.entries(this.currentWorker.installedPackages).map(([key, value]) => ({
            name: key,
            version: value
          })) : [];
    }
  }

  get userProfile() {
    return readUserProfile(this.$store);
  }

  public submit() {
    (this.$refs.observer as any).validate().then(() => {
      const currentProfile = readUserProfile(this.$store);
      const updatedProfile: UpdateMeDTO = {};
      if (this.displayName && this.displayName !== currentProfile?.displayName) {
        updatedProfile.displayName = this.displayName;
      }
      if (this.email && this.email !== currentProfile?.email) {
        updatedProfile.email = this.email;
      }
      if (Object.keys(updatedProfile).length > 0) {
        dispatchUpdateUserProfile(this.$store, updatedProfile).then(() => {
          this.editModeToggle = false;
          this.resetFormData();
        });
      } else {
        this.editModeToggle = false;
        this.resetFormData();
      }
    });
  }

  public async generateToken() {
    const loadingNotification = {content: 'Generating...', showProgress: true};
    try {
      commitAddNotification(this.$store, loadingNotification);
      commitRemoveNotification(this.$store, loadingNotification);
      this.apiAccessToken = await api.getApiAccessToken();
    } catch (error) {
      commitRemoveNotification(this.$store, loadingNotification);
      commitAddNotification(this.$store, {content: 'Could not reach server', color: 'error'});
    }
  }

  get giskardAddress() {
    return window.location.hostname;
  }

  public async copyToken() {
    await copyToClipboard(this.apiAccessToken?.id_token);
    commitAddNotification(this.$store, {content: "Copied to clipboard", color: "success"});
  }

  public async saveGeneralSettings(settings: GeneralSettings) {
    if (!settings.isAnalyticsEnabled) {
      mixpanel.opt_out_tracking();
    } else {
      mixpanel.opt_in_tracking();
    }
    this.appSettings!.generalSettings = await api.saveGeneralSettings(settings);
  }

  private epochToDate(epoch: number) {
    return moment.unix(epoch).format('DD/MM/YYYY HH:mm:ss');
  }

}
</script>
<style lang="scss" scoped>
.worker-tabs {
  width: auto;
  flex-grow: 0;
}

.token-area-wrapper {
  background-color: rgba(211, 211, 211, 0.52);
  padding: 10px;
}

.divider {
  margin-top: 10px;
  margin-bottom: 10px;
}

.token-area {
  user-select: all;
  word-break: break-all;
  font-size: 12px;
  font-family: monospace;
}

.worker-tab {
  display: flex;
  justify-content: space-between;
  width: 120px;
}

.giskard-address {
  border: 1px lightgrey dashed;
  padding: 2px;
}
</style>

