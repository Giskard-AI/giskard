<template>
  <v-container fluid class="vc">
    <v-row>
      <v-card elevation="2"
              :to="{name: 'test-suite-new', params: {suiteId: suite.id}}"
              class="ma-2"
              style="width: 300px"
              v-for="suite in suites">
        <v-card-title>{{ suite.name }}</v-card-title>
        <v-card-subtitle>Tests: {{ suite.tests.length }}</v-card-subtitle>
        <v-card-text>{{ suite.projectKey }}</v-card-text>
      </v-card>
    </v-row>
  </v-container>
</template>

<script lang="ts" setup>

import {api} from "@/api";
import {onMounted, ref} from "vue";
import {TestSuiteNewDTO} from "@/generated-sources";

const props = defineProps<{
  projectId: number
}>();

let suites = ref<TestSuiteNewDTO[]>([]);

onMounted(async () => {
  suites.value = await api.getTestSuitesNew(props.projectId);
})


</script>