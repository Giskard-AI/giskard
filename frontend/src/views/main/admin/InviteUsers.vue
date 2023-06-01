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
              <ValidationProvider name="Email" mode="eager" rules="email" v-slot="{ errors }">
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
            <v-btn small tile color="primaryLight" class="primaryLightBtn" @click="generateLink">Generate</v-btn>
            <v-btn v-if="link" small tile color="secondary" class="ml-2" @click="copyLink">
              Copy<v-icon right dark>mdi-content-copy</v-icon>
            </v-btn>
          </div>
          <div>
            <v-text-field v-if="link" v-model="link" readonly dense outlined hide-details class="my-0"></v-text-field>
            <span v-if="link" class="caption"><em>Note: link will be valid 72 hours</em></span>
          </div>
        </v-card-text>
      </v-card>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import {ref} from "vue";
import mixpanel from "mixpanel-browser";
import {api} from "@/api";
import {copyToClipboard} from "@/global-keys";
import {useMainStore} from "@/stores/main";
import {TYPE} from "vue-toastification";

const mainStore = useMainStore();

const emailToInvite = ref<string>("");
const link = ref<string>("");

async function sendEmail() {
  mixpanel.track('Invite user - email');
  if (emailToInvite.value) {
    const loadingNotification = { content: 'Sending...', showProgress: true };
    try {
      mainStore.addNotification(loadingNotification);
      await api.inviteToSignup(emailToInvite.value);
        mainStore.removeNotification(loadingNotification);
        mainStore.addNotification({content: 'User is invited', color: TYPE.SUCCESS});
        emailToInvite.value = "";
    } catch (error) {
        mainStore.removeNotification(loadingNotification);
        mainStore.addNotification({content: error.response.data.detail, color: TYPE.ERROR});
    }
  }
}

async function generateLink() {
  mixpanel.track('Invite user - generate link');
  const loadingNotification = { content: 'Generating...', showProgress: true };
  try {
    mainStore.addNotification(loadingNotification);
    const response = await api.getSignupLink();
    mainStore.removeNotification(loadingNotification);
    link.value = response;
  } catch (error) {
      mainStore.removeNotification(loadingNotification);
      mainStore.addNotification({content: 'Could not reach server', color: TYPE.ERROR});
  }
}

async function copyLink() {
    await copyToClipboard(link.value);
    mainStore.addNotification({content: "Copied to clipboard", color: TYPE.SUCCESS});
}
</script>
