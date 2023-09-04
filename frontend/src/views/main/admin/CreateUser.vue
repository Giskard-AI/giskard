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
        >You've reached the maximum number of users available with the current license
        </v-alert>
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
                      <v-text-field label="E-mail (unique)" type="email" v-model="email"
                                    :error-messages="errors"></v-text-field>
                    </ValidationProvider>
                    <ValidationProvider name="Password" mode="eager" rules="required|password" v-slot="{errors}">
                      <v-text-field type="password" autocomplete="new-password" ref="password" label="Password"
                                    v-model="password1" :error-messages="errors"></v-text-field>
                    </ValidationProvider>
                  </v-col>
                  <v-col cols=6>
                    <v-select label="Role" multiple v-model="roles" :items="allRoles" item-text="name"
                              item-value="id"></v-select>
                    <ValidationProvider name="Display name" mode="eager" rules="min:4" v-slot="{errors}">
                      <v-text-field label="Display Name" v-model="displayName" :error-messages="errors"></v-text-field>
                    </ValidationProvider>
                    <ValidationProvider name="Password confirmation" mode="eager" rules="required|confirms:@Password"
                                        v-slot="{errors}">
                      <v-text-field type="password" autocomplete="new-password" label="Confirm password"
                                    v-model="password2" :error-messages="errors"></v-text-field>
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

<script setup lang="ts">
import {Role} from "@/enums";
import mixpanel from "mixpanel-browser";
import {computed, onMounted, ref} from "vue";
import {useRouter} from "vue-router";
import {useMainStore} from "@/stores/main";
import {useAdminStore} from "@/stores/admin";

const router = useRouter();
const mainStore = useMainStore();
const adminStore = useAdminStore();

const observer = ref<any | null>(null);

const userId = ref<string>('');
const displayName = ref<string>('');
const email = ref<string>('');
const roles = ref<string[]>([Role.AICREATOR]);
const password1 = ref<string>('');
const password2 = ref<string>('');
const canAddUsers = ref<boolean>(true);

onMounted(async () => {
  await adminStore.getRoles();
  await adminStore.getUsers();
  const appSettings = await mainStore.appSettings;
  canAddUsers.value = !appSettings || !appSettings.seatsAvailable || appSettings.seatsAvailable > 0;
  reset();
})

const allRoles = computed(()=> {
  return adminStore.roles;
})

function reset() {
  userId.value = '';
  displayName.value = '';
  email.value = '';
  roles.value = [Role.AICREATOR];
  password1.value = '';
  password2.value = '';
  observer.value.reset();
}

function cancel() {
  router.back();
}

async function submit() {
  mixpanel.track('Create user', {login: userId.value, roles: roles.value});
  observer.value.validate().then(async () => {
    const profileCreate: AdminUserDTOWithPassword = {
      email: email.value,
      user_id: userId.value,
      roles: roles.value,
      password: password1.value
    };
    if (displayName.value) {
      profileCreate.displayName = displayName.value;
    }
    try {
      await adminStore.createUser(profileCreate);
      await router.push('/main/admin/users');
    } catch (e) {
      console.error(e.message);
    }
  });
}
</script>