<template>
  <v-card height="100%">
    <v-card-title class="font-weight-light secondary--text d-flex">
      <span>Running jobs</span>
      <v-spacer/>
      <v-btn icon @click="loadRunningJobs">
        <v-icon>refresh</v-icon>
      </v-btn>
    </v-card-title>
    <v-card-text>
      <v-alert
          v-if="runningJobs.length === 0"
          type="info"
      >
        No job are currently running on any worker
      </v-alert>
      <v-data-table v-else
                    :items="runningJobs"
                    :headers="tableHeaders"
      >
      </v-data-table>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">

import {computed, onMounted, ref} from 'vue';
import {WorkerJobDTO} from '@/generated-sources';
import {api} from '@/api';

const runningJobs = ref<WorkerJobDTO[]>([]);

async function loadRunningJobs() {
  runningJobs.value = await api.getRunningWorkerJobs();
}

onMounted(() => loadRunningJobs());

const tableHeaders = computed(() => [
  {
    text: "Execution date",
    sortable: true,
    value: "executionDate",
    align: "left",
  },
  {
    text: "Worker",
    sortable: true,
    value: "mlWorkerType",
    align: "left",
  },
]);

</script>
