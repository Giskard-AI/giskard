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

<script setup lang="ts">
import { Role } from '@/enums';
import mixpanel from 'mixpanel-browser';
import { api } from '@/api';
import { useRoute, useRouter } from 'vue-router/composables';
import { useAdminStore } from '@/stores/admin';
import { computed, onMounted, ref, watch } from 'vue';
import { AdminUserDTO } from '@/generated-sources';
import ButtonModalConfirmation from '@/components/ButtonModalConfirmation.vue';
import AdminUserDTOWithPassword = AdminUserDTO.AdminUserDTOWithPassword;

const router = useRouter();
const route = useRoute();
const adminStore = useAdminStore();

const displayName = ref<string>('');
const email = ref<string>('');
const roles = ref<string[] | null>([Role.AITESTER]);
const setPassword = ref<boolean>(false);
const password1 = ref<string>('');
const password2 = ref<string>('');

const observer = ref<any | null>(null);

onMounted(async () => {
  await adminStore.getRoles();
  await adminStore.getUsers();
  reset();
});

const allRoles = computed(() => {
  return adminStore.roles;
});


const user = computed(() => {
  return adminStore.getUser(parseInt(route.params.id));
});

watch(() => route.params.id, reset);

function reset() {
  setPassword.value = false;
  password1.value = '';
  password2.value = '';
  observer.value.reset();
  if (user.value) {
    displayName.value = user.value.displayName!;
    email.value = user.value.email;
    roles.value = user.value.roles!;
  }
}

function cancel() {
  router.back();
}

function submit() {
  mixpanel.track('Edit user', {login: user.value!.user_id, roles: roles.value});
  observer.value.validate().then(async () => {
    const updatedProfile: Partial<AdminUserDTOWithPassword> = {
      id: user.value!.id,
      user_id: user.value!.user_id,
      displayName: displayName.value,
      email: email.value,
      roles: roles.value,
    };
    if (setPassword.value && password1.value) {
      updatedProfile.password = password1.value;
    }
    await api.updateUser(updatedProfile);

    await router.push('/main/admin/users');
  });
}
</script>
