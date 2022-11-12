<template>
  <v-main>
    <v-container fluid fill-height>
      <v-layout align-center justify-center>
        <v-flex xs12 sm8 md4>
          <v-card class="elevation-12">
            <v-toolbar dark prominent :src="require('@/assets/wallpaper.jpg')">
              <v-toolbar-title>{{appName}} - Password Recovery</v-toolbar-title>
            </v-toolbar>
            <v-card-text>
              <p class="subtitle-1">Please enter your email address to receive a password recovery link</p>
              <v-text-field @keyup.enter="submit" label="Email" type="text" prepend-inner-icon="person" v-model="userId" required></v-text-field>
            </v-card-text>
            <v-card-actions>
              <v-spacer></v-spacer>
              <v-btn tile small class="secondary" @click="cancel">Cancel</v-btn>
              <v-btn tile small class="primary" @click.prevent="submit" :disabled="!valid">
                Recover Password
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-flex>
      </v-layout>
    </v-container>
  </v-main>
</template>

<script lang="ts">
import {Component, Vue} from 'vue-property-decorator';
import {appName} from '@/env';
import {dispatchPasswordRecovery} from '@/store/main/actions';

@Component
export default class Login extends Vue {
  public valid = true;
  public userId: string = '';
  public appName = appName;

  public cancel() {
    this.$router.back();
  }

  public submit() {
    if (this.userId) {
      dispatchPasswordRecovery(this.$store, { userId: this.userId });
    }
  }
}
</script>

<style>
div.v-image__image--cover{
  background-position: 15% 50% !important;
  background-size: auto;
}
</style>
