<template>
  <v-container fluid id="container-project-tab" class="vertical-container">
    <v-tabs>
      <v-tab to="/main/admin/general"><v-icon left>mdi-cog</v-icon>General</v-tab>
      <v-tab to="/main/admin/users"><v-icon left>people</v-icon>Users</v-tab>
    </v-tabs>
    <keep-alive>
      <router-view></router-view>
    </keep-alive>
  </v-container>
</template>

<script setup lang="ts">

</script>

<style scoped>

</style>