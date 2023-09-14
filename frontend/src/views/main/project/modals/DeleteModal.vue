<template>
  <v-dialog v-model="dialogOpened" width="500">
    <template v-slot:activator="{ on, attrs }">
      <v-tooltip bottom>
        <template v-slot:activator="{ onTooltip, attrsTooltip }" v-bind="attrs" v-on="on">
          <v-btn icon color="accent" @click.stop="openModal()" v-bind="attrsTooltip" v-on="onTooltip">
            <v-icon>delete</v-icon>
          </v-btn>
        </template>
        <span>Delete</span>
      </v-tooltip>
    </template>
    <v-card :loading="!usage">
      <v-card-title>Delete {{ props.type }}</v-card-title>
      <v-card-text v-if="usage">
        <v-container v-if="usage.totalUsage" class="pa-0">
          <v-row>
            <v-col>{{ capitalize(type) }} <span class="font-weight-bold">{{ fileName }}</span> is used by the
              following
              entities that will also be deleted:
            </v-col>
          </v-row>
          <v-row v-if="usage.suites?.length">
            <v-col cols="4">Test suites:</v-col>
            <v-col class="usage-container">
              <a v-for="s in usage.suites" @click="openSuite(s)">{{ s.name }}</a>
            </v-col>
          </v-row>
          <v-row v-if="usage.feedbacks?.length">
            <v-col cols="4">Inspection feedback:</v-col>
            <v-col class="usage-container">
              <a v-for="f in usage.feedbacks" @click="openFeedback(f)">{{ f.message }}</a>
            </v-col>
          </v-row>
        </v-container>
        <v-row class="pt-2">
          <v-col>
            <div v-if="usage.totalUsage">Are you sure you want to delete it?</div>
            <div v-else>Are you sure you want to delete {{ type }} <span class="font-weight-bold">{{
              fileName
            }}</span>?
            </div>
          </v-col>
        </v-row>
      </v-card-text>
      <v-card-text v-else>
        Loading information about {{ props.type }}...
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn color="primary" @click="dialogOpened = false; $emit('submit')">Delete</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { api } from "@/api";
import { capitalize } from "@vue/shared";
import { PrepareDeleteDTO } from "@/generated-sources";
import router from "@/router";

const emit = defineEmits(['submit'])

const props = defineProps<{
  type: "dataset" | "model"
  fileName: string
  id: string
}>();

const dialogOpened = ref<boolean>(false);
const usage = ref<PrepareDeleteDTO | null>(null);

function openSuite(suite: PrepareDeleteDTO.LightTestSuite) {
  router.push({
    name: "suite-details",
    params: {
      suiteId: suite.id.toString(),
      projectId: suite.projectId.toString()
    }
  });
}

function openFeedback(feedback: PrepareDeleteDTO.LightFeedback) {
  router.push({
    name: "project-feedback-detail",
    params: {
      feedbackId: feedback.id.toString(),
      projectId: feedback.projectId.toString()
    }
  });
}

async function openModal() {
  usage.value = null;
  dialogOpened.value = true;

  switch (props.type) {
    case "dataset":
      usage.value = await api.prepareDeleteDataset(props.id);
      break;
    case "model":
      usage.value = await api.prepareDeleteModel(props.id);
      break;
  }
}

</script>

<style lang="scss">
.usage-container {
  max-height: 100px;
  overflow: auto;
  display: flex;
  flex-direction: column;

  a {
    white-space: nowrap;
    min-height: 22px;
    overflow-x: hidden;
    text-overflow: ellipsis;
  }
}
</style>