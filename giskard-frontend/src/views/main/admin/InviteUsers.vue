<template>
<div>
  <v-toolbar flat dense light class="secondary--text text--lighten-2">
    <v-toolbar-title>
      <router-link to="/main/admin/users">
        Users
      </router-link>
      <span class="text-subtitle-1">
        <span class="mr-1">/</span>Invite
      </span>
    </v-toolbar-title>
  </v-toolbar>

  <v-container>
  <v-card>
    <v-card-text>
    <h3 class="font-weight-light mb-3">Enter email to send an invite:</h3>
    <v-row>
      <v-col shrink cols=3>
        <ValidationProvider name="Email" mode="eager" rules="email" v-slot="{errors}">
        <v-text-field v-model="emailToInvite" label="Email" dense outlined single-line :error-messages="errors"></v-text-field> 
        </ValidationProvider>
      </v-col>
      <v-col>
        <v-btn dense tile color="primary" @click="sendEmail"><v-icon left>send</v-icon>Send</v-btn>
      </v-col>
    </v-row>
    <v-divider class="my-2"></v-divider>
    <h3 class="font-weight-light mb-3">Or send your users the generated link:</h3>
    <div class="mb-2">
        <v-btn small tile color="primary" @click="generateLink">Generate</v-btn>
        <v-btn v-if="link" small tile color="secondary" class="ml-2" @click="copyLink">
            Copy<v-icon right dark>mdi-content-copy</v-icon>
        </v-btn>
    </div>
    <div>
      <v-text-field v-if="link" v-model="link" ref="link" readonly dense outlined hide-details class="my-0"></v-text-field>
      <span v-if="link" class="caption"><em>Note: link will be valid 72 hours</em></span>
    </div>
    </v-card-text>
  </v-card>
  </v-container>
</div>
</template>

<script lang="ts">
import { Component, Vue } from 'vue-property-decorator';
import { api } from '@/api';
import { commitAddNotification, commitRemoveNotification } from '@/store/main/mutations';
import { readToken } from '@/store/main/getters';

@Component
export default class AdminUsers extends Vue {

  public emailToInvite: string = "";
  public link: string = "";

  public async sendEmail() {
    if (this.emailToInvite) {
      const loadingNotification = { content: 'Sending...', showProgress: true };
      try {
          commitAddNotification(this.$store, loadingNotification);
          const response = await api.inviteToSignup(this.emailToInvite);
          commitRemoveNotification(this.$store, loadingNotification);
          commitAddNotification(this.$store, { content: 'User is invited', color: 'success'});
          this.emailToInvite = "";
      } catch (error) {
          commitRemoveNotification(this.$store, loadingNotification);
          commitAddNotification(this.$store, { content: error.response.data.detail, color: 'error' });
      }
    }
  }
  
  public async generateLink() {
    const loadingNotification = { content: 'Generating...', showProgress: true };
    try {
        commitAddNotification(this.$store, loadingNotification);
        const response = await api.getSignupLink();
        commitRemoveNotification(this.$store, loadingNotification);
        this.link = response;
    } catch (error) {
        commitRemoveNotification(this.$store, loadingNotification);
        commitAddNotification(this.$store, { content: 'Could not reach server', color: 'error' });
    }
  }

  public copyLink() {
    (this.$refs["link"] as Vue).$el.querySelector('input')?.select();
    document.execCommand("copy");
    commitAddNotification(this.$store, {content: "Copied to clipboard", color: "success"});
  }

}
</script>
