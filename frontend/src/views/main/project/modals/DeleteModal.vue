<template>
  <v-card :loading="!usage">
    <v-card-title>Delete {{ props.type }}</v-card-title>
    <v-card-text v-if="usage">
      <v-container v-if="usage.totalUsage" class="pa-0">
        <v-row>
          <v-col>{{ capitalize(type) }} <span class="font-weight-bold">{{ fileName }}</span> is used by the following
            entities that will also be deleted:
          </v-col>
        </v-row>
        <v-row v-if="usage.suiteCount" dense>
          <v-col cols="4">Test suites:</v-col>
          <v-col>{{ usage.suiteCount }}</v-col>
        </v-row>
        <v-row v-if="usage.feedbackCount" dense>
          <v-col cols="4">Inspection feedback:</v-col>
          <v-col>{{ usage.feedbackCount }}</v-col>
        </v-row>
      </v-container>
      <v-row class="pt-2">
        <v-col>
          <div v-if="usage.totalUsage">Are you sure you want to delete it?</div>
          <div v-else>Are you sure you want to delete {{ type }} <span class="font-weight-bold">{{ fileName }}</span>?
          </div>
        </v-col>
      </v-row>
    </v-card-text>
    <v-card-text v-else>
      Loading information about {{ props.type }}...
    </v-card-text>
    <v-card-actions>
      <v-spacer/>
      <v-btn color="primary" @click="$emit('submit', true)">Delete</v-btn>
    </v-card-actions>
  </v-card>

</template>

<script setup lang="ts">
import {onMounted, ref} from "vue";
import {api} from "@/api";
import {capitalize} from "@vue/shared";
import {PrepareDeleteDTO} from "@/generated-sources";

const props = defineProps<{
  type: "dataset" | "model"
  fileName: string
  id: number
}>();

const usage = ref<PrepareDeleteDTO | null>(null);


onMounted(async () => {
  switch (props.type) {
    case "dataset":
      usage.value = await api.prepareDeleteDataset(props.id);
      break;
    case "model":
      usage.value = await api.prepareDeleteModel(props.id);
      break;
  }
})
</script>