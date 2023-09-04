<template>
  <v-main>
    <v-container fluid class="fill-height">
      <v-layout align-center justify-center>
        <v-flex xs12 sm8 md4>
          <v-card class="elevation-12">
            <ValidationObserver ref="observer" v-slot="{ invalid }">
            <v-form @submit.prevent="">
            <v-toolbar dark prominent :src="require('@/assets/wallpaper.jpg')">
              <v-toolbar-title>{{appName}} - Reset Password</v-toolbar-title>
            </v-toolbar>
            <v-card-text>
              <p class="subheading">Enter your new password below</p>
                <ValidationProvider name="Password" mode="eager" rules="required|password" v-slot="{errors}">
                  <v-text-field type="password" autocomplete="new-password" ref="password" label="Password" v-model="password1" :error-messages="errors"></v-text-field>
                </ValidationProvider>
                <ValidationProvider name="Password confirmation" mode="eager" rules="required|confirms:@Password" v-slot="{errors}">
                  <v-text-field type="password" autocomplete="new-password" label="Confirm password" v-model="password2" :error-messages="errors"></v-text-field>
                </ValidationProvider>
            </v-card-text>
            <v-card-actions>
              <v-spacer></v-spacer>
              <v-btn tile small class="secondary" @click="cancel">Cancel</v-btn>
              <v-btn tile small class="secondary" @click="reset">Clear</v-btn>
              <v-btn tile small class="primary" @click="submit" :disabled="invalid">Save</v-btn>
            </v-card-actions>
            </v-form>
            </ValidationObserver>
          </v-card>
        </v-flex>
      </v-layout>
    </v-container>
  </v-main>
</template>

<script setup lang="ts">
import {appName as appname} from '@/env';
import mixpanel from "mixpanel-browser";
import {onMounted, ref} from "vue";
import {useRouter} from "vue-router";
import {useMainStore} from "@/stores/main";
import {useUserStore} from "@/stores/user";
import {TYPE} from "vue-toastification";

const router = useRouter();
const mainStore = useMainStore();
const userStore = useUserStore();

const appName = ref<string>(appname as string);
const password1 = ref<string>('');
const password2 = ref<string>('');

const observer = ref<any | null>(null);

onMounted(() => {
  checkToken();
})

function reset() {
  password1.value = '';
  password2.value = '';
  observer.value.reset();
}

function cancel() {
  router.push('/');
}

function checkToken() {
  const token = (router.currentRoute.value.query.token as string);
  if (!token) {
    mainStore.addNotification({
        content: 'No token provided in the URL, start a new password recovery',
        color: TYPE.ERROR,
    });
    router.push('/recover-password');
  } else {
    return token;
  }
}

async function submit() {
  mixpanel.track('Reset password');
  observer.value.validate().then(async () => {
    const token = checkToken();
    if (token) {
      await userStore.resetPassword({ token, password: password1.value });
      await router.push('/');
    }
  });
}
</script>

<style>
div.v-image__image--cover{
  background-position: 90% 40% !important;
  background-size: auto;
}
</style>
