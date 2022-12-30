<template>
  <router-view></router-view>
</template>

<script lang="ts">
import { Component, Vue } from 'vue-property-decorator';
import {useUserStore} from "@/stores/user";

const startRouteGuard = async (to, from, next) => {
  const userStore = useUserStore();
  await userStore.checkLoggedIn();
  if (userStore.isLoggedIn) {
    if (to.path === '/auth/login' || to.path === '/') {
      next('/main/dashboard');
    } else {
      next();
    }
  } else if (userStore.isLoggedIn === false) {
    if (to.path === '/' || (to.path as string).startsWith('/main')) {
      next('/auth/login');
    } else {
      next();
    }
  }
};

@Component
export default class Start extends Vue {
  public beforeRouteEnter(to, from, next) {
    startRouteGuard(to, from, next);
  }

  public beforeRouteUpdate(to, from, next) {
    startRouteGuard(to, from, next);
  }
}
</script>
