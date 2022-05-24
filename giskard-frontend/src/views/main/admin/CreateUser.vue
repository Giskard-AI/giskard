<template>
<div>
  <v-toolbar flat dense light class="secondary--text text--lighten-2">
    <v-toolbar-title>
      <router-link to="/main/admin/users">
        Users
      </router-link>
      <span class="text-subtitle-1">
        <span class="mr-1">/</span>New
      </span>
    </v-toolbar-title>
  </v-toolbar>

  <v-container>
    <v-card width="75%">
      <v-alert
          v-show="!canAddUsers"
          type="warning"
      >You've reached the maximum number of users available with the current license</v-alert>
      <ValidationObserver ref="observer" v-slot="{ invalid }">
      <v-form @submit.prevent="" :disabled="!canAddUsers">
      <v-container fluid>
      <v-card-text>
        <v-row>
          <v-col cols=6>
            <ValidationProvider name="User ID" mode="eager" rules="required|alpha_dash|min:4" v-slot="{errors}">
              <v-text-field label="User ID (unique)" v-model="userId" :error-messages="errors"></v-text-field>
            </ValidationProvider>
            <ValidationProvider name="Email" mode="eager" rules="required|email" v-slot="{errors}">
              <v-text-field label="E-mail (unique)" type="email" v-model="email" :error-messages="errors"></v-text-field>
            </ValidationProvider>
            <ValidationProvider name="Password" mode="eager" rules="required|password" v-slot="{errors}">
              <v-text-field type="password" autocomplete="new-password" ref="password" label="Password" v-model="password1" :error-messages="errors"></v-text-field>
            </ValidationProvider>
          </v-col>
          <v-col cols=6>
            <v-select label="Role" multiple v-model="roles" :items="allRoles" item-text="name" item-value="id"></v-select>
            <ValidationProvider name="Display name" mode="eager" rules="min:4" v-slot="{errors}">
            <v-text-field label="Display Name" v-model="displayName" :error-messages="errors"></v-text-field>
            </ValidationProvider>
            <ValidationProvider name="Password confirmation" mode="eager" rules="required|confirms:@Password" v-slot="{errors}">
              <v-text-field type="password" autocomplete="new-password" label="Confirm password" v-model="password2" :error-messages="errors"></v-text-field>
            </ValidationProvider>
          </v-col>
        </v-row>
      </v-card-text>
      <v-card-actions>
        <v-spacer/>
        <v-btn tile small class="secondary" @click="cancel">Cancel</v-btn>
        <v-btn tile small class="secondary" @click="reset">Reset</v-btn>
        <v-btn tile small class="primary" @click="submit" :disabled="invalid">Save</v-btn>
      </v-card-actions>
      </v-container>
      </v-form>
      </ValidationObserver>
    </v-card>
  </v-container>
</div>
</template>

<script lang="ts">
import { Component, Vue } from 'vue-property-decorator';
import {dispatchCreateUser, dispatchGetRoles, dispatchGetUsers} from '@/store/admin/actions';
import { readAdminRoles } from '@/store/admin/getters';
import {readAppSettings} from "@/store/main/getters";
import { AdminUserDTO } from '@/generated-sources';
import AdminUserDTOWithPassword = AdminUserDTO.AdminUserDTOWithPassword;
import { Role } from '@/enums';

@Component
export default class CreateUser extends Vue {

  $refs!: {
    observer
  }

  public userId: string = '';
  public displayName: string = '';
  public email: string = '';
  public roles: string[] = [Role.AICREATOR];
  public password1: string = '';
  public password2: string = '';
  public canAddUsers: boolean = true;

  public async mounted() {
    await dispatchGetRoles(this.$store);
    await dispatchGetUsers(this.$store);
    const appSettings = await readAppSettings(this.$store);
    this.canAddUsers = !appSettings || !appSettings.seats_available || appSettings.seats_available > 0;
    this.reset();

  }

  get allRoles() {
    return readAdminRoles(this.$store);
  }

  public reset() {
    this.userId = '';
    this.displayName = '';
    this.email = '';
    this.roles = [Role.AICREATOR];
    this.password1 = '';
    this.password2 = '';
    this.$refs.observer.reset();
  }

  public cancel() {
    this.$router.back();
  }

  public async submit() {
    this.$refs.observer.validate().then(async () => {
      const profileCreate: AdminUserDTOWithPassword = {
        email: this.email,
        user_id: this.userId,
        roles: this.roles,
        password: this.password1
      };
      if (this.displayName) {
        profileCreate.displayName = this.displayName;
      }
      try {
        await dispatchCreateUser(this.$store, profileCreate);
        await this.$router.push('/main/admin/users');
      } catch (e) {
        console.error(e.message);
      }
    });
  }
}
</script>
