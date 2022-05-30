<template>
  <div>
    <v-toolbar flat dense light class="secondary--text text--lighten-2">
      <v-toolbar-title>
        <router-link to="/main/admin/users">
          Users
        </router-link>
        <span class="text-subtitle-1">
        <span class="mr-1">/</span>Edit
        <span class="mr-1">/</span>{{ user.user_id }}
      </span>
      </v-toolbar-title>
    </v-toolbar>
    <v-container>
      <v-card width="75%">
        <ValidationObserver ref="observer" v-slot="{ invalid, pristine }">
          <v-form @submit.prevent="">
            <v-container fluid>
              <v-card-text>
                <v-row>
                  <v-col cols=6>
                    <v-text-field label="User ID" v-model="user.user_id" disabled></v-text-field>
                    <ValidationProvider name="Email" mode="eager" rules="required|email" v-slot="{errors}">
                      <v-text-field label="E-mail (unique)" type="email" v-model="email"
                                    :error-messages="errors"></v-text-field>
                    </ValidationProvider>
                    <v-checkbox dense v-model="setPassword" label="Change password"></v-checkbox>
                  </v-col>
                  <v-col cols=6>
                    <ValidationProvider name="Role" mode="eager" v-slot="{errors}">
                      <v-select label="Role" multiple v-model="roles" :items="allRoles" item-text="name" item-value="id"
                                :error-messages="errors"></v-select>
                    </ValidationProvider>
                    <ValidationProvider name="Display name" mode="eager" rules="min:4" v-slot="{errors}">
                      <v-text-field label="Display Name" v-model="displayName" :error-messages="errors"></v-text-field>
                    </ValidationProvider>
                  </v-col>
                </v-row>
                <v-row class="mt-0">
                  <v-col cols=6>
                    <ValidationProvider name="Password" mode="eager" rules="password" v-slot="{errors}">
                      <v-text-field dense type="password" autocomplete="new-password" ref="password" label="Password"
                                    v-model="password1" :error-messages="errors"
                                    :disabled="!setPassword"></v-text-field>
                    </ValidationProvider>
                  </v-col>
                  <v-col cols=6>
                    <ValidationProvider name="Password confirmation" mode="eager" rules="confirms:@Password"
                                        v-slot="{errors}">
                      <v-text-field dense type="password" autocomplete="new-password" label="Confirm password"
                                    v-model="password2" :error-messages="errors"
                                    :disabled="!setPassword"></v-text-field>
                    </ValidationProvider>
                  </v-col>
                </v-row>
              </v-card-text>
              <v-card-actions>
                <v-spacer/>
                <v-btn tile small class="secondary" @click="cancel">Cancel</v-btn>
                <v-btn tile small class="secondary" @click="reset">Reset</v-btn>
                <ButtonModalConfirmation
                    title="Please confirm action"
                    :text="'Editing user ' + user.user_id"
                    :disabledButton="invalid || pristine"
                    @ok="submit">
                </ButtonModalConfirmation>
              </v-card-actions>
            </v-container>
          </v-form>
        </ValidationObserver>
      </v-card>
    </v-container>
  </div>
</template>

<script lang="ts">
import {Component, Vue} from 'vue-property-decorator';
import {dispatchGetRoles, dispatchGetUsers} from '@/store/admin/actions';
import {readAdminOneUser, readAdminRoles} from '@/store/admin/getters';
import ButtonModalConfirmation from '@/components/ButtonModalConfirmation.vue';
import {AdminUserDTO} from '@/generated-sources';
import {Role} from '@/enums';
import {api} from "@/api";
import AdminUserDTOWithPassword = AdminUserDTO.AdminUserDTOWithPassword;

@Component({
  components: {
    ButtonModalConfirmation,
  },
})
export default class EditUser extends Vue {
  public displayName: string = '';
  public email: string = '';
  public roles?: string[] | null = [Role.AITESTER];
  public setPassword = false;
  public password1: string = '';
  public password2: string = '';

  $refs!: {
    observer
  }

  public async mounted() {
    await dispatchGetRoles(this.$store);
    await dispatchGetUsers(this.$store);
    this.reset();
  }

  get allRoles() {
    return readAdminRoles(this.$store);
  }

  get user() {
    return readAdminOneUser(this.$store)(parseInt(this.$router.currentRoute.params.id));
  }

  public reset() {
    this.setPassword = false;
    this.password1 = '';
    this.password2 = '';
    this.$refs.observer.reset();
    if (this.user) {
      this.displayName = this.user.displayName!;
      this.email = this.user.email;
      this.roles = this.user.roles;
    }
  }

  public cancel() {
    this.$router.back();
  }

  public submit() {
    this.$refs.observer.validate().then(async () => {
      const updatedProfile: Partial<AdminUserDTOWithPassword> = {
        id: this.user!.id,
        user_id: this.user!.user_id,
        displayName: this.displayName,
        email: this.email,
        roles: this.roles,
      };
      if (this.setPassword && this.password1) {
        updatedProfile.password = this.password1;
      }
      await api.updateUser(updatedProfile);

      await this.$router.push('/main/admin/users');
    });
  }

}
</script>
