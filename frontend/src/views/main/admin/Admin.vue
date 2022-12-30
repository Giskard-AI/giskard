<template>
  <Settings/>
</template>

<script lang="ts">
import { Component, Vue } from 'vue-property-decorator';
import Settings from "@/views/main/admin/settings/Settings.vue";
import {useUserStore} from "@/stores/user";

const routeGuardAdmin = async (to, from, next) => {
  const userStore = useUserStore();
  if (!userStore.hasAdminAccess) {
    next('/main');
  } else {
    next();
  }
};

@Component({
  components: {Settings}
})
export default class Admin extends Vue {
  public beforeRouteEnter(to, from, next) {
    routeGuardAdmin(to, from, next);
  }

  public beforeRouteUpdate(to, from, next) {
    routeGuardAdmin(to, from, next);
  }
}
</script>
