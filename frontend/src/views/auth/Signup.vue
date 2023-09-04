<template>
  <div style="width: 320px">
    <ValidationObserver ref="observer" v-slot="{ invalid }">
      <v-form @keyup.enter="submit">
        <ValidationProvider name="User ID" mode="eager" rules="required|alpha_dash|min:4" v-slot="{errors}">
          <v-text-field v-model="userId" prepend-inner-icon="vpn_key" label="User ID" type="text"
                        autocomplete="username" dense outlined :error-messages="errors"></v-text-field>
        </ValidationProvider>
        <ValidationProvider name="Display name" mode="eager" rules="min:4" v-slot="{errors}">
          <v-text-field v-model="displayName" prepend-inner-icon="person" label="Display name" type="text"
                        autocomplete="name" dense outlined :error-messages="errors"></v-text-field>
        </ValidationProvider>
        <ValidationProvider name="Email" mode="eager" rules="required|email" v-slot="{errors}">
          <v-text-field v-model="email" :disabled="hasEmailParam" prepend-inner-icon="email" label="Email" type="email"
                        autocomplete="email" dense outlined :error-messages="errors"></v-text-field>
        </ValidationProvider>
        <ValidationProvider name="Password" mode="eager" rules="required|password" v-slot="{errors}">
          <v-text-field v-model="password" prepend-inner-icon="lock" label="Password" id="password" type="password"
                        autocomplete="new-password" dense outlined :error-messages="errors"></v-text-field>
        </ValidationProvider>
        <ValidationProvider name="Password confirmation" mode="eager" rules="required|confirms:@Password"
                            v-slot="{errors}">
          <v-text-field v-model="passwordConfirm" prepend-inner-icon="lock" label="Confirm password"
                        id="passwordConfirm" type="password" autocomplete="new-password" dense outlined
                        :error-messages="errors"></v-text-field>
        </ValidationProvider>
        <div class="d-flex justify-space-between align-center">
          <v-btn block color="primary" type="input" @click.prevent="submit" :disabled="invalid || !hasTokenParam">Create
            account
          </v-btn>
        </div>
        <div v-if="errorMsg" class="text-body-2 error--text mt-2">
          {{ errorMsg }}
        </div>
        <div class="my-2 text-center">
          <span class="caption"><router-link to="/auth/login">Already have an account?</router-link></span>
        </div>
      </v-form>
    </ValidationObserver>
  </div>
</template>

<script setup lang="ts">
import {ManagedUserVM} from "@/generated-sources";
import {onMounted, ref} from "vue";
import {useRouter} from "vue-router";
import {useUserStore} from "@/stores/user";
import {useMainStore} from "@/stores/main";
import {TYPE} from "vue-toastification";

const router = useRouter();
const userStore = useUserStore();
const mainStore = useMainStore();

const userId = ref<string>('');
const displayName = ref<string>('');
const email = ref<string>('');
const password = ref<string>('');
const passwordConfirm = ref<string>('');
const errorMsg = ref<string>('');
const hasTokenParam = ref<boolean>(false);
const hasEmailParam = ref<boolean>(false);

const observer = ref<any | null>(null);

onMounted(() => {
  checkToken();
  if (router.currentRoute.value.query.to) {
    email.value = (router.currentRoute.value.query.to as string);
    hasEmailParam.value = true;
  }
})

function checkToken() {
  const token = (router.currentRoute.value.query.token as string);
  if (!token) {
    errorMsg.value = "Disabled because no token is provided in the URL"
    hasTokenParam.value = false;
  } else {
    errorMsg.value = ""
    hasTokenParam.value = true;
    return token;
  }
}

async function submit() {
  observer.value.validate().then(async () => {
    const token = checkToken();
    if (token) {
      const profileCreate: ManagedUserVM = {
        email: email.value,
        user_id: userId.value,
        password: password.value,
        token: token
      };
      if (displayName.value) {
        profileCreate.displayName = displayName.value;
      }
      try {
        await userStore.signupUser({userData: profileCreate});
        await router.push('/');
      } catch (e: any) {
        errorMsg.value = e.message;
      }
    } else {
      mainStore.addNotification({
        content: 'No token provided in the URL',
        color: TYPE.ERROR,
      });
    }
  });
}
</script>
