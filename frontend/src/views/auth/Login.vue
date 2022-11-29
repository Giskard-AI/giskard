<template>
  <div style="width: 260px">
    <v-form @keyup.enter="submit">
      <v-text-field @keyup.enter="submit" v-model="login" prepend-inner-icon="person" name="login" label="User ID or Email" type="text" autocomplete="username" dense outlined></v-text-field>
      <v-text-field @keyup.enter="submit" v-model="password" prepend-inner-icon="lock" name="password" label="Password" id="password" type="password" autocomplete="current-password" dense outlined></v-text-field>
    </v-form>
    <div class="d-flex justify-space-between align-center">
      <v-btn block 
            @click="submit()"
            color="primary"
            :disabled="isLoggingIn"
            :loading='isLoggingIn'>Login</v-btn>
    </div>
    <div v-if="loginError" class="text-body-2 error--text mt-2">
      {{loginError}}
    </div>
    <div class="my-2 text-center">
      <span class="caption"><router-link to="/recover-password">Forgot your password?</router-link></span>
    </div>
  </div>
</template>

<script lang="ts">
import { Component, Vue } from 'vue-property-decorator';
import { readLoginError } from '@/store/main/getters';
import { dispatchLogIn } from '@/store/main/actions';
import { commitAddNotification } from '@/store/main/mutations';

@Component
export default class Login extends Vue {
  public login: string = '';
  public password: string = '';
  public isLoggingIn = false;

  public get loginError() {
    return readLoginError(this.$store);
  }

  public async submit() {
    if (this.login && this.password) {
      this.isLoggingIn = true;
      await dispatchLogIn(this.$store, {username: this.login, password: this.password});
      this.isLoggingIn = false;
    } else {
        commitAddNotification(this.$store, {
          content: 'Please enter credentials',
          color: 'error',
        });
      }
  }
}
</script>

<style scoped>
</style>
