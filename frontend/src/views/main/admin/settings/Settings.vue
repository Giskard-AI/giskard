<template>
  <div class="vc">
    <v-toolbar flat dense light class="secondary--text text--lighten-2 mt-2">
      <v-toolbar-title class="text-body-1">
        <router-link to="/main/admin" class="font-weight-bold" id="page-title">
          Settings
        </router-link>
      </v-toolbar-title>
    </v-toolbar>
    <v-tabs v-if="tabs.length > 1">
      <v-tab v-for="tab in tabs" :to="tab.to">
        <v-icon left>{{ tab.icon }}</v-icon>
        {{ tab.text }}
      </v-tab>
    </v-tabs>
    <div class="vc fill-height">
      <keep-alive>
        <router-view></router-view>
      </keep-alive>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useMainStore } from "@/stores/main";

const mainStore = useMainStore();

interface Tab {
  to: string,
  icon: string,
  text: string
}

const tabs = ref<Tab[]>([]);

onMounted(() => {
  tabs.value = [
    { to: "/main/admin/general", icon: "mdi-cog", text: "General" }
  ]

  if (mainStore.authAvailable) {
    tabs.value.push({ to: "/main/admin/users", icon: "people", text: "Users" })
  }
})

</script>
<style scoped>
#page-title {
  font-size: 1.125rem !important;
}
</style>
