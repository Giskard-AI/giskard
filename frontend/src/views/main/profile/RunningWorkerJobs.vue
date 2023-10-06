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

import {onMounted, ref} from 'vue';
import {openapi} from "@/api-v2";
import {JobDTO} from "@/generated/client";

const runningJobs = ref<Array<JobDTO>>([]);

async function loadRunningJobs() {
  runningJobs.value = await openapi.mlWorkerJob.getRunningWorkerJobs();
}

onMounted(() => loadRunningJobs());

const tableHeaders = [
  {
    text: "Execution date",
    sortable: true,
    value: "scheduledDate",
    align: "left",
  },
  {
    text: "State",
    sortable: true,
    value: "state",
    align: "left",
  },
  {
    text: "Type",
    sortable: true,
    value: "jobType",
    align: "left",
  },
  {
    text: "Worker",
    sortable: true,
    value: "mlWorkerType",
    align: "left",
  },
];

</script>
