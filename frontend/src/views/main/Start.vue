<template>
  <router-view></router-view>
</template>

<script lang="ts">
import {Component, Vue} from 'vue-property-decorator';
import {useUserStore} from "@/stores/user";
import {useMainStore} from "@/stores/main";

const startRouteGuard = async (to, from, next) => {
  const userStore = useUserStore();
  const mainStore = useMainStore();

  await userStore.checkLoggedIn();

  if (!mainStore.license?.active) {
    if (to.path !== '/setup') {
      next('/setup');
    } else {
      next();
    }
  } else if (userStore.isLoggedIn) {
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
