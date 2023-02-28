<template>
  <v-container class="mt-7">
    <v-row>
      <v-col>
        <img src="@/assets/logo_v2_full.png" alt="logo" width="480">
      </v-col>
    </v-row>
    <v-row v-if="!done">
      <v-col>
        <v-card>
          <v-card-title>I need a license</v-card-title>
          <v-card-text>
            Giskard requires a license to use its UI. You can get a FREE open source license mailed to you via the form
            below. If you already have one, you can upload it on the right hand side of this page.

            <v-form>
              <v-text-field label="First name" v-model="firstName"></v-text-field>
              <v-text-field label="Last name" v-model="lastName"></v-text-field>
              <v-text-field label="Email" v-model="email"></v-text-field>
              <v-text-field label="Company name" v-model="companyName"></v-text-field>
              <v-btn :loading="loading" text @click="submit">Submit</v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>
      <v-divider vertical></v-divider>
      <v-col>
        <v-card>
          <v-card-title>I have a license</v-card-title>
          <v-card-text>
            If you already have a license, you can upload your license file by pressing the button below.
          </v-card-text>
          <v-card-actions class="ml-2 mb-2">
            <v-btn small color="primary" @click="openFileInput">Upload license file</v-btn>
            <input type="file" ref="fileInput" style="display: none;" @change="onFileUpdate"/>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
    <v-row v-if="done">
      <v-col>
        <v-card>
          <v-card-title>Thank you for installing Giskard</v-card-title>
          <v-card-text>You will be redirected to the app in a few seconds. If this does not happen, <a
              @click="redirectToMain">click here</a>.
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">

import {ref} from "vue";
import axios, {AxiosError} from "axios";
import {useMainStore} from "@/stores/main";
import {api} from "@/api";
import {useRouter} from "vue-router/composables";

const router = useRouter();

const loading = ref<boolean>(false);
const done = ref<boolean>(false);

const mainStore = useMainStore();

const fileInput = ref<any | null>(null);
const firstName = ref<string>("");
const lastName = ref<string>("");
const email = ref<string>("");
const companyName = ref<string>("");

async function submit() {
  try {
    loading.value = true;
    await axios.post('https://hook.eu1.make.com/g81venzbf3ausl6b8xitgudtqo4ev39q', {
      firstName: firstName.value,
      lastName: lastName.value,
      email: email.value,
      companyName: companyName.value
    });
    loading.value = false;
    mainStore.addNotification({color: 'success', content: "License request submitted, please check your email!"});
  } catch (e: AxiosError) {
    mainStore.addNotification({color: 'error', content: e.response?.data.toString()});
  }
}

function openFileInput() {
  fileInput.value?.click();
}

async function onFileUpdate(event) {
  let formData = new FormData();
  formData.append('file', event.target.files[0]);

  await api.uploadLicense(formData);
  await mainStore.fetchAppSettings();
  done.value = true;
  setTimeout(() => redirectToMain(), 3000);
}

function redirectToMain() {
  router.push("/");
}

</script>