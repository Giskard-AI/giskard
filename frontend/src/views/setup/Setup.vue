<template>
  <v-container class="mt-7">
    <v-row>
      <v-col>
        <img src="@/assets/logo_v2_full.png" alt="logo" width="480">
      </v-col>
    </v-row>
    <v-row v-if="mainStore.license && !mainStore.license.active && mainStore.license.licenseProblem">
      <v-col>
        <v-alert type="warning" outlined prominent dense>
          <v-card flat>
            <v-card-title>The current license is invalid</v-card-title>
            <v-card-text>{{ mainStore.license.licenseProblem }}</v-card-text>
          </v-card>
        </v-alert>
      </v-col>
    </v-row>
    <template v-if="mainStore.license && mainStore.license.active && !mainStore.license.licenseProblem">
      <v-row>
        <v-col>
          <v-alert type="success" outlined prominent color="primary" dense>
            <v-card flat>
              <v-card-title>The current license is valid <span v-if="mainStore.license.expiresOn">&nbsp;until {{ mainStore.license.expiresOn | date }}</span></v-card-title>
              <v-card-text>
                <v-btn tile color="primary" :to="{ name: 'main-dashboard' }">Open Giskard</v-btn>
              </v-card-text>
            </v-card>
          </v-alert>
        </v-col>
      </v-row>
      <v-row>
        <v-col class="text-center">If you want to update your license follow the steps below</v-col>
      </v-row>
    </template>

    <v-row>
      <v-col>
        <v-stepper v-model="step" vertical>
          <v-stepper-step step="1" :complete="step > 1">
            Request a license
            <small v-if="licenseRequestSubmitted" style="color: green;">Your license request was submitted, please check
              your email.</small>
          </v-stepper-step>
          <v-stepper-content step="1" class="px-0">
            <p class="pl-6">
              Giskard server requires a license. If you don't have one, you can request a <span class="font-weight-bold">free</span> license by filling the form below.
            </p>
            <p class="pl-6">
              The license will be <span class="font-weight-bold">sent by email</span>. You don't need to submit a new request if you already have one.
            </p>

            <div class="pl-6 py-4 mt-8">
              <span class="has-license-question">Do you already have a license?</span> <span class="has-license-question-sub">*check your mailbox if you are not sure</span>
              <v-radio-group v-model="hasLicense" row>
                <v-radio label="Yes" value="2" @click="step = 2"></v-radio>
                <v-radio label="No" value="1"></v-radio>
              </v-radio-group>
            </div>
            <div class="pl-6 py-4" v-show="hasLicense === '1'">
              <span class="has-license-question pb-2">Fill the form below to get your license</span>
              <ValidationObserver ref="observer" v-slot="{ invalid }">
                <v-form @keyup.enter="submit" style="max-width: 500px" class="">
                  <ValidationProvider name="First name" mode="eager" rules="required" v-slot="{ errors }">
                    <v-text-field label="First name*" v-model="firstName" :error-messages="errors" required></v-text-field>
                  </ValidationProvider>
                  <ValidationProvider name="Last name" mode="eager" rules="required" v-slot="{ errors }">
                    <v-text-field label="Last name*" v-model="lastName" :error-messages="errors"></v-text-field>
                  </ValidationProvider>
                  <ValidationProvider name="Email" mode="eager" rules="required|email" v-slot="{ errors }">
                    <v-text-field label="Email*" v-model="email" :error-messages="errors" type="email"></v-text-field>
                  </ValidationProvider>
                  <ValidationProvider name="Company name" mode="eager" rules="required" v-slot="{ errors }">
                    <v-text-field label="Company name*" v-model="companyName" :error-messages="errors"></v-text-field>
                  </ValidationProvider>
                  <ValidationProvider name="Agreement with the privacy policy" mode="eager" :rules="{ required: { allowFalse: false } }" v-slot="{ errors }">

                    <v-checkbox v-model="termsOfServiceAgree" dense :error-messages="errors">
                      <template v-slot:label>
                        <span>I agree to the <a @click.stop href="https://giskard-ai.github.io/giskard-privacy/policy.html">privacy
                            policy</a></span>
                      </template>
                    </v-checkbox>
                  </ValidationProvider>
                  <v-checkbox v-model="newsLetterAgree" dense label="I agree to receive newsletters and updates about Giskard"></v-checkbox>
                  <v-btn :loading="loading" color="primary" @click.prevent="submit" :disabled="invalid">Submit</v-btn>
                </v-form>
              </ValidationObserver>
            </div>
          </v-stepper-content>

          <v-stepper-step step="2" :complete="step > 2">
            Select license file
          </v-stepper-step>
          <v-stepper-content step="2">
            <p>You should have received your license file by <span class="font-weight-bold">email</span>.</p>
            <p>Upload it below to complete the setup.</p>

            <v-btn color="primary" class="mb-1" @click="openFileInput">
              <v-icon left>mdi-upload</v-icon>
              Upload license file
            </v-btn>
            <v-btn text color="secondary" class="mb-1 ml-2" @click="() => { step = 1; hasLicense = '1' }">I don't have a license</v-btn>
            <input type="file" ref="fileInput" style="display: none;" @change="onFileUpdate" />
          </v-stepper-content>

          <v-stepper-step step="3" :complete="step >= 3">
            Launch Giskard
          </v-stepper-step>
          <v-stepper-content step="3">
            <p>Your Giskard setup is now complete! You can now refresh this page or click the button below to open
              Giskard.</p>

            <v-btn color="primary" large @click="finalizeSetup()" class="mb-1">Launch Giskard</v-btn>
          </v-stepper-content>
        </v-stepper>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">

import { ref } from "vue";
import axios, { AxiosError } from "axios";
import { useMainStore } from "@/stores/main";
import { api } from "@/api";
import { useRouter } from "vue-router";
import mixpanel from "mixpanel-browser";
import { TYPE } from "vue-toastification";

const router = useRouter();

const loading = ref<boolean>(false);
const step = ref<number>(1);
const hasLicense = ref<string>();

const mainStore = useMainStore();

const fileInput = ref<any | null>(null);
const firstName = ref<string>("");
const lastName = ref<string>("");
const email = ref<string>("");
const companyName = ref<string>("");
const termsOfServiceAgree = ref<boolean>(false);
const newsLetterAgree = ref<boolean>(false);
const analyticsAgree = ref<boolean>(true);

const licenseRequestSubmitted = ref<boolean>(false);

const observer = ref<any | null>(null);

let licenseContents: string = "";

async function submit() {
  observer.value.validate().then(async (passed) => {
    if (!passed) {
      return;
    }

    try {
      loading.value = true;
      licenseRequestSubmitted.value = false;
      await axios.post('https://hook.eu1.make.com/g81venzbf3ausl6b8xitgudtqo4ev39q', {
        firstName: firstName.value,
        lastName: lastName.value,
        email: email.value,
        companyName: companyName.value,
        newsletter: newsLetterAgree.value,
        tos: termsOfServiceAgree.value
      });
      step.value = 2;
      licenseRequestSubmitted.value = true;
      mainStore.addNotification({
        color: TYPE.SUCCESS,
        content: "License request submitted, please check your email!"
      });
    } catch (e: AxiosError) {
      mainStore.addNotification({ color: TYPE.ERROR, content: e.response?.data.toString() });
    } finally {
      loading.value = false;
    }
  });
}

function openFileInput() {
  fileInput.value?.click();
}

async function onFileUpdate(event) {
  if (!event.target.files[0]) {
    return;
  }

  const reader = new FileReader();

  reader.onload = (ev) => {
    licenseContents = <string>ev.target.result;

    // Simple check to make sure the file uploaded is the right one.
    if (licenseContents.startsWith("-----BEGIN LICENSE FILE-----")) {
      step.value = 3;
    } else {
      mainStore.addNotification({
        color: TYPE.ERROR,
        content: 'License file format is not valid.'
      });
    }
  };

  reader.readAsText(event.target.files[0]);
}

async function finalizeSetup() {
  if (analyticsAgree.value) {
    mixpanel.opt_in_tracking();
  } else {
    mixpanel.opt_out_tracking();
  }

  await api.finalizeSetup(analyticsAgree.value, licenseContents);
  await mainStore.fetchLicense();
  await router.push("/main/dashboard");
}

</script>
<style scoped lang="scss">
.has-license-question {
  font-size: 1.1rem;
  opacity: 0.8;
}

.has-license-question-sub {
  font-size: 0.9rem;
  font-weight: bold;
}
</style>
