<template>
  <v-container fluid id="container-project-tab" class="vertical-container">
    <v-tabs v-if="tabs.length > 1">
      <v-tab v-for="tab in tabs" :to="tab.to">
        <v-icon left>{{ tab.icon }}</v-icon>
        {{ tab.text }}
      </v-tab>
    </v-tabs>
    <keep-alive>
      <router-view></router-view>
    </keep-alive>
  </v-container>
</template>

<script setup lang="ts">
import {onMounted, ref} from "vue";
import {useMainStore} from "@/stores/main";

const mainStore = useMainStore();

interface Tab {
  to: string,
  icon: string,
  text: string
}

const tabs = ref<Tab[]>([]);

// TODO: Check featureflags?
onMounted(() => {
  tabs.value = [
    {to: "/main/admin/general", icon: "mdi-cog", text: "General"}
  ]

  if (mainStore.authAvailable) {
    tabs.value.push({to: "/main/admin/users", icon: "people", text: "Users"})
  }
})

</script>

<style scoped>

</style>