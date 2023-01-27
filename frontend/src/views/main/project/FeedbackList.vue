<template>
  <div>
    <v-toolbar flat dense light class="mt-2 blue-grey lighten-5">
      <v-select
          dense
          solo
          hide-details
          clearable
          class="mx-2 flex-1"
          :items="existingModels"
          v-model="modelFilter"
          placeholder="Model"
      ></v-select>
      <v-select
          dense
          solo
          hide-details
          clearable
          class="mx-2 flex-1"
          :items="existingDatasets"
          v-model="datasetFilter"
          placeholder="Dataset"
      ></v-select>
      <v-select
          dense
          solo
          hide-details
          clearable
          class="mx-2 flex-1"
          :items="existingTypes"
          v-model="typeFilter"
          placeholder="Type"
      ></v-select>
      <v-text-field
          dense
          solo
          hide-details
          clearable
          class="mx-2 flex-1"
          v-model="search"
          append-icon="mdi-magnify"
          label="Search"
      ></v-text-field>
      <v-checkbox
          single-line
          hide-details
          class="mx-2 flex-1"
          label="Group by feature"
          v-model="groupByFeature"
      ></v-checkbox>
      <v-btn text dense
             @click="fetchFeedbacks()"
             color="secondary"
      >Reload
        <v-icon right>refresh</v-icon>
      </v-btn>
    </v-toolbar>
    <v-container fluid>
      <v-data-table
          dense
          :group-by="groupByFeature ? 'featureName': null"
          :items="feedbacks"
          :headers="tableHeaders"
          :search="search"
          :items-per-page="25"
          :footer-props="{
            'items-per-page-options': [10, 25, 50, 100]
          }"
          @click:row="openFeedback"
      >
        <!-- eslint-disable-next-line vue/valid-v-slot -->
        <template v-slot:item.createdOn="{ item }">
          <span>{{ item.createdOn | date }}</span>
        </template>
        <!-- eslint-disable-next-line vue/valid-v-slot -->
        <template v-slot:item.featureValue="{ item }">
          <span>{{
              (item.featureValue && item.featureValue.length > 140) ? item.featureValue.slice(0, 140) + "..." : item.featureValue
            }}</span>
        </template>
        <template v-slot:item.action="{item}"
                  v-slot:item.id="{item}">
          <v-btn
              icon
              @click.stop="deleteFeedback(item)"
              @click.stop.prevent
          >
            <v-icon color="accent">delete</v-icon>
          </v-btn>
        </template>
      </v-data-table>
    </v-container>
    <v-dialog width="90vw" v-model="openFeedbackDetail" @input="handleFeedbackDetailDialogClosed">
      <router-view/>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import {api} from "@/api";
import {FeedbackMinimalDTO} from "@/generated-sources";
import {computed, onActivated, ref, watch} from 'vue';
import {useRoute, useRouter} from 'vue-router/composables';
import {$vfm} from 'vue-final-modal';
import ConfirmModal from '@/views/main/project/modals/ConfirmModal.vue';

const route = useRoute();
const router = useRouter();

const { projectId } = defineProps<{ projectId: number }>();


const feedbacks = ref<FeedbackMinimalDTO[]>([]);
const search = ref<string>('');
const modelFilter = ref<string>('');
const datasetFilter = ref<string>('');
const typeFilter = ref<string>('');
const groupByFeature = ref<boolean>(false);
const openFeedbackDetail = ref<boolean>(false);

onActivated(() => {
  fetchFeedbacks();
  handleRouteChanged();
});

async function fetchFeedbacks() {
  feedbacks.value = await api.getProjectFeedbacks(projectId);
}

async function openFeedback(obj) {
  await router.push({name: 'feedback-detail', params: {feedbackId: obj.id}})
}

function handleRouteChanged() {
  openFeedbackDetail.value = route.meta && route.meta.openFeedbackDetail
}

watch(() => route.meta, () => handleRouteChanged());

function handleFeedbackDetailDialogClosed(isOpen) {
  if (!isOpen && route.name !== 'project-feedbacks') {
    router.push({name: 'project-feedbacks'});
  }
}

const tableHeaders = computed(() => [
  {
    text: "Model",
    sortable: true,
    value: "modelName",
    align: "left",
    filter: (value) => !modelFilter.value ? true : value == modelFilter.value,
  },
  {
    text: "Dataset",
    sortable: true,
    value: "datasetName",
    align: "left",
    filter: (value) => !datasetFilter.value ? true : value == datasetFilter.value,
  },
  {
    text: "User ID",
    sortable: true,
    value: "userLogin",
    align: "left",
  },
  {
    text: 'On',
    value: 'createdOn',
    sortable: true,
    filterable: false,
    align: 'left'
  },
  {
    text: "Type",
    sortable: true,
    value: "feedbackType",
    align: "left",
    filter: (value) => !typeFilter.value ? true : value == typeFilter.value,
  },
  {
    text: "Feature name",
    sortable: true,
    value: "featureName",
    align: "left",
  },
  {
    text: "Feature value",
    sortable: true,
    value: "featureValue",
    align: "left",
  },
  {
    text: "Choice",
    sortable: true,
    value: "feedbackChoice",
    align: "left",
  },
  {
    text: "Message",
    sortable: true,
    value: "feedbackMessage",
    align: "left",
  },
  {
    sortable: false,
    filterable: false,
    text: 'Actions',
    value: 'action'
  }
]);

const existingModels = computed(() => feedbacks.value.map((e) => e.modelName));
const existingDatasets = computed(() => feedbacks.value.map((e) => e.datasetName));
const existingTypes = computed(() => feedbacks.value.map((e) => e.feedbackType));

function deleteFeedback(feedback: FeedbackMinimalDTO) {
  $vfm.show({
    component: ConfirmModal,
    bind: {
      title: 'Delete feedback',
      text: `Are you sure that you want to delete the feedback for feature '${feedback.featureName}' permanently?`,
      isWarning: true
    },
    on: {
      async confirm(close) {
        await api.deleteFeedback(feedback.id);
        await fetchFeedbacks();
        close();
      }
    }
  });
}

}
</script>

<style scoped>
div.v-input.flex-1 {
  flex: 1 /* ugly, but no other idea */
}

.v-data-table >>> tbody > tr {
  cursor: pointer;
}
</style>
