<template>
  <div class="vc">
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
import {onMounted, ref} from "vue";
import {useMainStore} from "@/stores/main";

const mainStore = useMainStore();

interface Tab {
  to: string,
  icon: string,
  text: string
}

const tabs = ref<Tab[]>([]);

onMounted(() => {
  tabs.value = [
    {to: "/main/admin/general", icon: "mdi-cog", text: "General"}
  ]

  if (mainStore.authAvailable) {
    tabs.value.push({to: "/main/admin/users", icon: "people", text: "Users"})
  }
})

</script>
