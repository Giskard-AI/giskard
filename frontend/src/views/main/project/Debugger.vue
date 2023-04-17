<script setup lang="ts">
import { ref } from "vue";

const inspections = ref([0]);
const searchInspection = ref("");

function createInspection() {
  console.log("Create inspection");
}
</script>

<template>
  <v-container fluid class="vc" v-if="inspections.length > 0">
    <v-row>
      <v-col cols="4">
        <v-text-field label="Search inspection" append-icon="search" outlined v-model="searchInspection"></v-text-field>
      </v-col>
      <v-col cols="8">
        <div class="d-flex flex-row-reverse pb-4">
          <v-btn color="primary" @click="createInspection"><v-icon>add</v-icon> New Inspection</v-btn>
        </div>
      </v-col>
    </v-row>
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