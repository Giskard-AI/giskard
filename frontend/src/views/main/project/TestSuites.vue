<template>
  <v-container fluid class="vc" v-if="suites.length > 0">
    <div class="d-flex flex-row-reverse pb-4">
      <v-btn
          color="primary"
          @click="createTestSuite"
      >
        New test suite
      </v-btn>
    </div>
    <v-row>
      <v-card elevation="2"
              :to="{name: 'test-suite-overview', params: {suiteId: suite.id}}"
              class="ma-2"
              style="width: 300px"
              v-for="suite in suites">
        <v-card-title>{{ suite.name }}</v-card-title>
        <v-card-subtitle>Tests: {{ suite.tests.length }}</v-card-subtitle>
        <v-card-text>{{ suite.projectKey }}</v-card-text>
      </v-card>
    </v-row>
  </v-container>
  <v-container v-else class="d-flex flex-column vc fill-height">
    <h1 class="pt-16">You haven't created any test suite for this project!</h1>
    <v-btn tile class='mx-1'
           @click="createTestSuite"
           color="primary">
      <v-icon>add</v-icon>
      Create a new test suite
    </v-btn>
  </v-container>
</template>

<script lang="ts" setup>

import {api} from "@/api";
import {onMounted, ref} from "vue";
import CreateTestSuiteModal from '@/views/main/project/modals/CreateTestSuiteModal.vue';
import {$vfm} from 'vue-final-modal';
import {TestSuiteDTO} from '@/generated-sources';

const props = defineProps<{
  projectId: number
}>();

const suites = ref<TestSuiteDTO[]>([]);

onMounted(async () => suites.value = await api.getTestSuites(props.projectId))

async function createTestSuite() {
  const project = await api.getProject(props.projectId)
  $vfm.show({
    component: CreateTestSuiteModal,
    bind: {
      projectKey: project.key,
      projectId: project.id
    }
  });
}

</script>
