<template>
  <v-main>
    <v-container fluid fill-height>
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

<script lang="ts">
import { Component, Vue } from 'vue-property-decorator';
import { appName } from '@/env';
import { commitAddNotification } from '@/store/main/mutations';
import { dispatchResetPassword } from '@/store/main/actions';
import mixpanel from "mixpanel-browser";

@Component
export default class UserProfileEdit extends Vue {
  public appName = appName;
  public password1 = '';
  public password2 = '';

  public mounted() {
    this.checkToken();
  }

  public reset() {
    this.password1 = '';
    this.password2 = '';
    (this.$refs.observer as any).reset();
  }

  public cancel() {
    this.$router.push('/');
  }

  public checkToken() {
    const token = (this.$router.currentRoute.query.token as string);
    if (!token) {
      commitAddNotification(this.$store, {
        content: 'No token provided in the URL, start a new password recovery',
        color: 'error',
      });
      this.$router.push('/recover-password');
    } else {
      return token;
    }
  }

  public async submit() {
    mixpanel.track('Reset password');
    (this.$refs.observer as any).validate().then(async () => {
      const token = this.checkToken();
      if (token) {
        await dispatchResetPassword(this.$store, { token, password: this.password1 });
        await this.$router.push('/');
      }
    });
  }
}
</script>

<style>
div.v-image__image--cover{
  background-position: 90% 40% !important;
  background-size: auto;
}
</style>
