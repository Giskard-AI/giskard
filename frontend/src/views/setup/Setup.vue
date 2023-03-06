<template>
  <v-container class="mt-7">
    <v-row>
      <v-col>
        <img src="@/assets/logo_v2_full.png" alt="logo" width="480">
      </v-col>
    </v-row>
    <v-row v-if="!done">
      <v-col>
        <v-card class="fill-height">
          <v-card-title>Request a license</v-card-title>
          <v-card-text>
            <p>
              Giskard server requires a license. A <span class="font-weight-bold">free</span> license can be obtained by
              registered using the form below. The license will be sent by email.
            </p>
            <p>If you already have one, you can upload it on the right hand side of this page.</p>
            <ValidationObserver ref="observer" v-slot="{ invalid }">
              <v-form @keyup.enter="submit">
                <ValidationProvider name="First name" mode="eager" rules="required" v-slot="{errors}">
                  <v-text-field label="First name" v-model="firstName" :error-messages="errors"></v-text-field>
                </ValidationProvider>
                <ValidationProvider name="Last name" mode="eager" rules="required" v-slot="{errors}">
                  <v-text-field label="Last name" v-model="lastName" :error-messages="errors"></v-text-field>
                </ValidationProvider>
                <ValidationProvider name="Email" mode="eager" rules="required|email" v-slot="{errors}">
                  <v-text-field label="Email" v-model="email" :error-messages="errors"></v-text-field>
                </ValidationProvider>
                <v-text-field label="Company name" v-model="companyName"></v-text-field>
                <v-btn :loading="loading" color="primary" @click.prevent="submit">Submit</v-btn>
              </v-form>
            </ValidationObserver>
          </v-card-text>
        </v-card>
      </v-col>
      <v-divider vertical class="ma-10"></v-divider>
      <v-col>
        <v-card class="fill-height">
          <v-card-title>Use existing license</v-card-title>
          <v-card-text class="flex-grow-1">
            If you already have a license, you can upload your license file by pressing the button below.
          </v-card-text>
          <v-card-actions class="ml-2 mb-2 justify-center">
            <v-btn color="primary" @click="openFileInput">Upload license file</v-btn>
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

const observer = ref<any | null>(null);

async function submit() {
  observer.value.validate().then(async (passed) => {
    if (!passed) {
      return;
    }

    try {
      loading.value = true;
      await axios.post('https://hook.eu1.make.com/g81venzbf3ausl6b8xitgudtqo4ev39q', {
        firstName: firstName.value,
        lastName: lastName.value,
        email: email.value,
        companyName: companyName.value
      });
      mainStore.addNotification({color: 'success', content: "License request submitted, please check your email!"});
    } catch (e: AxiosError) {
      mainStore.addNotification({color: 'error', content: e.response?.data.toString()});
    } finally {
      loading.value = false;
    }
  });
}

function openFileInput() {
  fileInput.value?.click();
}

async function onFileUpdate(event) {
  let formData = new FormData();
  formData.append('file', event.target.files[0]);

  await api.uploadLicense(formData);
  await mainStore.fetchLicense();
  done.value = true;
  setTimeout(() => redirectToMain(), 3000);
}

function redirectToMain() {
  router.push("/main/dashboard");
}

</script>