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

<script setup lang="ts">
import {computed, ref} from "vue";
import {useUserStore} from "@/stores/user";
import {UpdateMeDTO} from "@/generated-sources";
import {useRouter} from "vue-router";
import ButtonModalConfirmation from "@/components/ButtonModalConfirmation.vue";

const userStore = useUserStore();
const router = useRouter();

const valid = ref<boolean>(true);
const password1 = ref<string>('');
const password2 = ref<string>('');

const observer = ref<any | null>(null);

const userProfile = computed(() => {
  return userStore.userProfile;
});

function reset() {
  password1.value = '';
  password2.value = '';
  observer.value.reset();
}

function cancel() {
  router.back();
}

function submit() {
  observer.value.validate().then(async () => {
    const updatedProfile: UpdateMeDTO = {
      password : password1.value
    };
    await userStore.updateUserProfile(updatedProfile);
    await router.push('/main/profile');
  })
}
</script>