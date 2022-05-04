<template>
  <div style="width: 320px">
    <ValidationObserver ref="observer" v-slot="{ invalid }">
        <v-form @keyup.enter="submit">
            <ValidationProvider name="User ID" mode="eager" rules="required|alpha_dash|min:4" v-slot="{errors}">
            <v-text-field v-model="userId" prepend-inner-icon="vpn_key" label="User ID" type="text" autocomplete="username" dense outlined :error-messages="errors"></v-text-field>
            </ValidationProvider>
            <ValidationProvider name="Display name" mode="eager" rules="min:4" v-slot="{errors}">
            <v-text-field v-model="displayName" prepend-inner-icon="person" label="Display name" type="text" autocomplete="name" dense outlined :error-messages="errors"></v-text-field>
            </ValidationProvider>
            <ValidationProvider name="Email" mode="eager" rules="required|email" v-slot="{errors}">
            <v-text-field v-model="email" :disabled="hasEmailParam" prepend-inner-icon="email" label="Email" type="email" autocomplete="email" dense outlined :error-messages="errors"></v-text-field>
            </ValidationProvider>
            <ValidationProvider name="Password" mode="eager" rules="required|password" v-slot="{errors}">
            <v-text-field v-model="password" prepend-inner-icon="lock" label="Password" id="password" type="password" autocomplete="new-password" dense outlined :error-messages="errors"></v-text-field>
            </ValidationProvider>
            <ValidationProvider name="Password confirmation" mode="eager" rules="required|confirms:@Password" v-slot="{errors}">
            <v-text-field v-model="passwordConfirm" prepend-inner-icon="lock" label="Confirm password" id="passwordConfirm" type="password" autocomplete="new-password" dense outlined :error-messages="errors"></v-text-field>
            </ValidationProvider>
            <div class="d-flex justify-space-between align-center">
                <v-btn block color="primary" type="input" @click.prevent="submit" :disabled="invalid || !hasTokenParam">Create account</v-btn>
            </div>
            <div v-if="errorMsg" class="text-body-2 error--text mt-2">
                {{errorMsg}}
            </div>
            <div class="my-2 text-center">
              <span class="caption"><router-link to="/auth/login">Already have an account?</router-link></span>
            </div>
        </v-form>
    </ValidationObserver>
  </div>
</template>

<script lang="ts">
import { Component, Vue } from 'vue-property-decorator';
import { dispatchSignupUser } from '@/store/main/actions';
import { commitAddNotification } from '@/store/main/mutations';
import { AdminUserDTO, ManagedUserVM } from '@/generated-sources';
import AdminUserDTOWithPassword = AdminUserDTO.AdminUserDTOWithPassword;

@Component
export default class Login extends Vue {
  $refs!: {
    observer
  }

  public userId: string = '';
  public displayName: string = '';
  public email: string = '';
  public password: string = '';
  public passwordConfirm: string = '';

  private errorMsg: string = '';
  private hasTokenParam: boolean = false;
  private hasEmailParam: boolean = false;

  public mounted() {
    this.checkToken();
    if (this.$router.currentRoute.query.to) {
      this.email = (this.$router.currentRoute.query.to as string);
      this.hasEmailParam = true;
    }
  }

  public checkToken() {
    const token = (this.$router.currentRoute.query.token as string);
    if (!token) {
      this.errorMsg = "Disabled because no token is provided in the URL"
      this.hasTokenParam = false;
    } else {
      this.errorMsg = ""
      this.hasTokenParam = true;
      return token;
    }
  }

  public async submit() {
    this.$refs.observer.validate().then(async () => {
      const token = this.checkToken();
      if (token) {
        const profileCreate: ManagedUserVM = {
          email: this.email,
          user_id: this.userId,
          password: this.password,
          token: token
        };
        if (this.displayName) {
          profileCreate.displayName = this.displayName;
        }
        try {
          await dispatchSignupUser(this.$store, {userData: profileCreate});
          this.$router.push('/');
        } catch (e) {
          this.errorMsg = e.message;
        }
      } else {
        commitAddNotification(this.$store, {
          content: 'No token provided in the URL',
          color: 'error',
        });
      }
    });
  }
}
</script>

<style scoped>
</style>
