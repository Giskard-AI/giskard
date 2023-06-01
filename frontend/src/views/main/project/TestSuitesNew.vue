<template>
  <v-container fluid class="vc">
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
import CreateTestSuiteModal from '@/views/main/project/modals/CreateTestSuiteModal.vue';
import {$vfm} from 'vue-final-modal';

const props = defineProps<{
  projectId: number
}>();

const suites = ref<TestSuiteNewDTO[]>([]);

onMounted(async () =>  suites.value = await api.getTestSuitesNew(props.projectId))

async function createTestSuite() {
  const project = await api.getProject(props.projectId)
  $vfm.show({
    component: CreateTestSuiteModal,
    bind: {
      projectKey: project.key
    }
  });
}

</script>
