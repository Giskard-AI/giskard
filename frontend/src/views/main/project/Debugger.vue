<script setup lang="ts">
import { ref } from "vue";

const inspections = ref([]);

function createInspection() {
  console.log("Create inspection");
}
</script>

<template>
  <v-container fluid class="vc" v-if="inspections.length > 0">
    <p>Lorem ipsum dolor sit amet consectetur adipisicing elit. Temporibus autem ea corporis expedita, quaerat illum, cupiditate dolores dolor quia perferendis ab doloribus, magnam aliquam voluptatum laborum neque similique recusandae ducimus dolore iste tenetur sequi! Aliquam, ut!</p>
  </v-container>
  <v-container v-else class="d-flex flex-column vc fill-height">
    <h1 class="pt-16">You haven't created any inspection for this project!</h1>
    <v-btn tile class='mx-1'
           @click="createInspection"
           color="primary">
      <v-icon>add</v-icon>
      Create a new inspection
    </v-btn>
  </v-container>
</template>

<style scoped>
</style>