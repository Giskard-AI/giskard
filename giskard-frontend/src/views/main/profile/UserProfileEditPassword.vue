<template>
<div>
  <v-toolbar flat dense light>
    <v-toolbar-title class="secondary--text text--lighten-2">
      <router-link to="/main/profile">
        My Profile
      </router-link>
      <span class="text-subtitle-1">
        <span class="mr-1">/</span>Change password
      </span>
    </v-toolbar-title>
  </v-toolbar>

  <v-container>
    <v-card width="40%">
      <ValidationObserver ref="observer" v-slot="{ invalid }">
      <v-form @submit.prevent="">
      <v-container fluid>
        <v-card-text>
            <v-row>
              <v-col>
                <v-text-field label="User ID" autocomplete="username" v-model="userProfile.user_id" disabled></v-text-field>
                <ValidationProvider name="Password" mode="eager" rules="required|password" v-slot="{errors}">
                  <v-text-field type="password" autocomplete="new-password" ref="password" label="Password" v-model="password1" :error-messages="errors"></v-text-field>
                </ValidationProvider>
                <ValidationProvider name="Password confirmation" mode="eager" rules="required|confirms:@Password" v-slot="{errors}">
                  <v-text-field type="password" autocomplete="new-password" label="Confirm password" v-model="password2" :error-messages="errors"></v-text-field>
                </ValidationProvider>
              </v-col>
            </v-row>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn tile small class="secondary" @click="cancel">Cancel</v-btn>
          <v-btn tile small class="secondary" @click="reset">Clear</v-btn>
          <ButtonModalConfirmation 
            :disabledButton="invalid"
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
import {readUserProfile} from '@/store/main/getters';
import {dispatchUpdateUserProfile} from '@/store/main/actions';
import ButtonModalConfirmation from '@/components/ButtonModalConfirmation.vue';
import {AdminUserDTO, UpdateMeDTO} from '@/generated-sources';

@Component({
  components: {
    ButtonModalConfirmation,
  },
})
export default class UserProfileEdit extends Vue {
  public valid = true;
  public password1 = '';
  public password2 = '';

  get userProfile() {
    return readUserProfile(this.$store);
  }

  public reset() {
    this.password1 = '';
    this.password2 = '';
    (this.$refs.observer as any).reset();
  }

  public cancel() {
    this.$router.back();
  }

  public submit() {
    (this.$refs.observer as any).validate().then(async () => {
      const updatedProfile: UpdateMeDTO = {
        password : this.password1
      };
      await dispatchUpdateUserProfile(this.$store, updatedProfile);
      await this.$router.push('/main/profile');
    })
  }
}
</script>
