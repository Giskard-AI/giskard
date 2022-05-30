<template>
<div>
  <v-toolbar flat dense light>
    <v-toolbar-title class="text-h6 font-weight-regular secondary--text text--lighten-1">
      My Profile
    </v-toolbar-title>
  </v-toolbar>
  <v-container>
    <div v-if="userProfile">
    <v-card width="50%">
      <ValidationObserver ref="observer" v-slot="{ invalid, pristine }">
        <v-form @submit.prevent="">
          <v-card-title class="font-weight-light secondary--text">Details</v-card-title>
          <v-card-text>
            <v-row>
              <v-col cols=6>
                <div>
                  <div class="caption secondary--text text--lighten-3">User ID</div>
                  <div class="subtitle-1">{{userProfile.user_id}}</div>
                </div>
                <div class="mt-3">
                  <div class="caption secondary--text text--lighten-3">Display Name</div>
                  <div v-if="!editModeToggle">
                    <div class="subtitle-1" v-if="userProfile.displayName">{{userProfile.displayName}}</div>
                    <div class="subtitle-1" v-else>(not set)</div>
                  </div>
                  <div v-else>
                    <ValidationProvider name="Display name" mode="eager" rules="min:4" v-slot="{errors}">
                     <v-text-field v-model="displayName" single-line :error-messages="errors" class="my-0 py-0"></v-text-field>
                    </ValidationProvider>
                  </div>
                </div>
              </v-col>
              <v-col cols=6>
                <div>
                  <div class="caption secondary--text text--lighten-3">Roles</div>
                  <div class="subtitle-1" v-for='role in userProfile.roles'>{{role | roleName}}</div>
                </div>
                <div class="mt-3">
                  <div class="caption secondary--text text--lighten-3">Email</div>
                  <div v-if="!editModeToggle" class="subtitle-1">{{userProfile.email}}</div>
                  <div v-else>
                    <ValidationProvider name="Email" mode="eager" rules="required|email" v-slot="{errors}">
                      <v-text-field type="email" v-model="email" single-line hide :error-messages="errors" class="my-0 py-0"></v-text-field>
                    </ValidationProvider>
                  </div>
                </div>
              </v-col>
            </v-row>
          </v-card-text>
      
          <v-card-actions class="px-4 pb-4">
            <v-btn tile small color="accent" to="/main/profile/password">Change password</v-btn>
            <v-spacer></v-spacer>
            <v-btn tile small class="primary" v-show="!editModeToggle" @click="editModeToggle = true" >Edit</v-btn>
            <v-btn tile small class="secondary" v-show="editModeToggle" @click="editModeToggle = false; resetFormData();">Cancel</v-btn>
            <ButtonModalConfirmation 
              v-if="editModeToggle" 
              :disabledButton="invalid || pristine" 
              @ok="submit">
            </ButtonModalConfirmation>
          </v-card-actions>
        </v-form>
      </ValidationObserver>
    </v-card>

    <v-card width="50%" class="my-2">
      <v-card-title class="font-weight-light secondary--text">API Access Token</v-card-title>
      <v-card-text>
        <div class="mb-2">
            <v-btn small tile color="primary" @click="generateToken">Generate</v-btn>
            <v-btn v-if="apiAccessToken" small tile color="secondary" class="ml-2" @click="copyToken">
                Copy<v-icon right dark>mdi-content-copy</v-icon>
            </v-btn>
        </div>
        <v-text-field v-if="apiAccessToken" v-model="apiAccessToken" ref="apiAccessToken" readonly dense outlined hide-details class="my-0"></v-text-field>
      </v-card-text>
    </v-card>
    </div>
    <div v-else>Not found</div>
  </v-container>
</div>
</template>

<script lang="ts">
import {Component, Vue} from 'vue-property-decorator';
import {readToken, readUserProfile} from '@/store/main/getters';
import {api} from '@/api';
import {commitAddNotification, commitRemoveNotification} from '@/store/main/mutations';
import {dispatchUpdateUserProfile} from '@/store/main/actions';
import ButtonModalConfirmation from '@/components/ButtonModalConfirmation.vue';
import {UpdateMeDTO} from '@/generated-sources';

@Component({
  components: {
    ButtonModalConfirmation,
  },
})
export default class UserProfile extends Vue {

  private displayName: string = '';
  private email: string = '';
  private editModeToggle = false;
  private apiAccessToken: string = '';

  private resetFormData() {
    const userProfile = readUserProfile(this.$store);
    if (userProfile) {
      if (userProfile.displayName) {
        this.displayName = userProfile.displayName;
      }
      this.email = userProfile.email;
    }
  }

  public created() {
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
        }).catch(() => {}) 
      } else {
        this.editModeToggle = false;
        this.resetFormData();
      }
    });
  }

  public async generateToken() {
    const loadingNotification = { content: 'Generating...', showProgress: true };
    try {
        commitAddNotification(this.$store, loadingNotification);
        commitRemoveNotification(this.$store, loadingNotification);
        this.apiAccessToken = (await api.getApiAccessToken()).id_token;
    } catch (error) {
        commitRemoveNotification(this.$store, loadingNotification);
        commitAddNotification(this.$store, { content: 'Could not reach server', color: 'error' });
    }
  }

  public copyToken() {
    (this.$refs["apiAccessToken"] as Vue).$el.querySelector('input')?.select();
    document.execCommand("copy");
    commitAddNotification(this.$store, {content: "Copied to clipboard", color: "success"});
  }

}
</script>
