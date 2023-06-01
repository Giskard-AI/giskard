<template>
  <div>
    <div class="text-center">Add test to an existing test suite</div>
    <v-list>
      <v-list-item v-for="s in testSuites">
        <v-list-item-content>{{ s.name }}</v-list-item-content>
      </v-list-item>
    </v-list>
    <v-btn tile small>Create a new test suite</v-btn>
    <div>
      <v-btn tile small>Back</v-btn>
    </div>
  </div>
</template>

<script setup lang="ts">
import {ref} from "vue";

const testSuites = ref([])

</script>

<style scoped>
.v-list-item {
  border-bottom: 1px solid lightgrey;
}
</style>