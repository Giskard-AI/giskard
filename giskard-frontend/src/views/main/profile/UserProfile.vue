<template>
  <div>
    <v-toolbar flat dense light>
      <v-toolbar-title class="text-h6 font-weight-regular secondary--text text--lighten-1">
        My Profile
      </v-toolbar-title>
    </v-toolbar>
    <v-container>
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
                  <tr><td colspan="2"><v-divider/></td></tr>
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
        <v-col v-show="isAdmin">
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
    </v-container>
  </div>
</template>

<script lang="ts">
import {Component, Vue} from 'vue-property-decorator';
import {readAppSettings, readUserProfile} from '@/store/main/getters';
import {api} from '@/api';
import {commitAddNotification, commitRemoveNotification} from '@/store/main/mutations';
import {dispatchUpdateUserProfile} from '@/store/main/actions';
import ButtonModalConfirmation from '@/components/ButtonModalConfirmation.vue';
import {copyToClipboard} from '@/global-keys';
import {AppConfigDTO, GeneralSettings, JWTToken, UpdateMeDTO} from "@/generated-sources";
import mixpanel from "mixpanel-browser";
import {Role} from "@/enums";
import AppInfoDTO = AppConfigDTO.AppInfoDTO;

@Component({
  components: {
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
    this.resetFormData();
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

}
</script>
<style lang="scss" scoped>
.token-area-wrapper {
  background-color: rgba(211, 211, 211, 0.52);
  padding: 10px;
}

.token-area {
  user-select: all;
  word-break: break-all;
  font-size: 12px;
  font-family: monospace;
}
</style>

