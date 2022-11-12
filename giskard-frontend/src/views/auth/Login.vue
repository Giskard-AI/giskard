<template>
  <div style="width: 260px">
    <v-form @keyup.enter="submit">
      <v-text-field @keyup.enter="submit" v-model="login" prepend-inner-icon="person" name="login"
                    label="User ID or Email" type="text" autocomplete="username" dense outlined></v-text-field>
      <v-text-field @keyup.enter="submit" v-model="password" prepend-inner-icon="lock" name="password" label="Password"
                    id="password" type="password" autocomplete="current-password" dense outlined></v-text-field>
    </v-form>
    <div class="d-flex justify-space-between align-center">
      <v-btn block @click.prevent="submit" color="primary">Login</v-btn>
    </div>
    <div v-if="loginStore.loginError" class="text-body-2 error--text mt-2">
      {{ loginStore.loginError }}
    </div>
    <div class="my-2 text-center">
      <span class="caption"><router-link to="/recover-password">Forgot your password?</router-link></span>
    </div>
  </div>
</template>

<script lang="ts" setup>
import {ref} from "vue";
import {useLoginStore} from "@/store/pinia/login";

const login = ref(null);
const password = ref(null);

const loginStore = useLoginStore();


async function submit() {
  if (login.value && password.value) {
    await loginStore.logIn({username: login.value, password: password.value})
  } else {
    loginStore.addNotification({
      content: 'Please enter credentials',
      color: 'error',
    });
  }
}
</script>

