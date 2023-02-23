<template>
  <v-container class="mt-7">
    <v-row>
      <v-col>
        <img src="@/assets/logo_v2_full.png" alt="logo" width="480">
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <v-card>
          <v-card-title>I need a license</v-card-title>
          <v-card-text>
            Giskard requires a license to use its UI! You can get a FREE open source license mailed to you via the form
            below. If you already have one, you can paste it on the right hand side of this page.

            <v-form>
              <v-text-field label="First name" v-model="firstName"></v-text-field>
              <v-text-field label="Last name" v-model="lastName"></v-text-field>
              <v-text-field label="Email" v-model="email"></v-text-field>
              <v-text-field label="Company name" v-model="companyName"></v-text-field>
            </v-form>

            <v-btn text @click="submit">Submit</v-btn>
          </v-card-text>
        </v-card>
      </v-col>
      <v-divider vertical></v-divider>
      <v-col>
        <v-card>
          <v-card-title>I have a license</v-card-title>
          <v-card-text>
            <v-btn small color="primary" @click="openFileInput">Upload license file</v-btn>
            <input type="file" ref="fileInput" style="display: none;" @change="onFileUpdate"/>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">

import {ref} from "vue";
import axios from "axios";
import {useMainStore} from "@/stores/main";
import {api} from "@/api";


const mainStore = useMainStore();

const fileInput = ref<any | null>(null);
const currentStep = ref<number>(1);

const firstName = ref<string>("");
const lastName = ref<string>("");
const email = ref<string>("");
const companyName = ref<string>("");

async function submit() {
  // TODO: While waiting for the email template to be done, submitting automatically inputs the license ....
  const license = await axios.post('https://hook.eu1.make.com/g81venzbf3ausl6b8xitgudtqo4ev39q', {
    firstName: firstName.value,
    lastName: lastName.value,
    email: email.value,
    companyName: companyName.value
  })
}

function openFileInput() {
  fileInput.value?.click();
}

async function onFileUpdate(event) {
  let formData = new FormData();
  formData.append('file', event.target.files[0]);

  await api.uploadLicense(formData);
  await mainStore.fetchAppSettings();
}

</script>