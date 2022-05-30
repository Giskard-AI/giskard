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
      </v-data-table>
    </v-container>
    <v-dialog width="90vw" v-model="openFeedbackDetail" @click:outside="$router.push({name: 'project-feedbacks'})">
      <router-view/>
    </v-dialog>
  </div>
</template>

<script lang="ts">
import {Component, Prop, Vue, Watch} from "vue-property-decorator";
import {api} from "@/api";
import {readToken} from "@/store/main/getters";
import {commitAddNotification} from '@/store/main/mutations';
import FeedbackDetail from './FeedbackDetail.vue';
import {FeedbackMinimalDTO} from "@/generated-sources";

@Component({
  components: {FeedbackDetail}
})
export default class FeedbackList extends Vue {
  @Prop({required: true}) projectId!: number;

  feedbacks: FeedbackMinimalDTO[] = [];
  search = "";
  modelFilter = "";
  datasetFilter = "";
  typeFilter = "";
  groupByFeature = false

  openFeedbackDetail = false

  activated() {
    this.fetchFeedbacks();
    this.setOpenFeedbackDetail(this.$route)
  }

  @Watch("$route", {deep: true})
  setOpenFeedbackDetail(to) {
    this.openFeedbackDetail = to.meta && to.meta.openFeedbackDetail
  }

  get tableHeaders() {
    return [
      {
        text: "Model",
        sortable: true,
        value: "modelName",
        align: "left",
        filter: (value) => !this.modelFilter ? true : value == this.modelFilter,
      },
      {
        text: "Dataset",
        sortable: true,
        value: "datasetName",
        align: "left",
        filter: (value) => !this.datasetFilter ? true : value == this.datasetFilter,
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
        filter: (value) => !this.typeFilter ? true : value == this.typeFilter,
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
    ];
  }

  get existingModels() {
    return this.feedbacks.map((e) => e.modelName);
  }

  get existingDatasets() {
    return this.feedbacks.map((e) => e.datasetName);
  }

  get existingTypes() {
    return this.feedbacks.map((e) => e.feedbackType);
  }

  public async fetchFeedbacks() {
    try {
      this.feedbacks = await api.getProjectFeedbacks(this.projectId);
    } catch (error) {
      commitAddNotification(this.$store, {content: error.response.data.detail, color: 'error'});
    }
  }

  public async openFeedback(obj) {
    await this.$router.push({name: 'feedback-detail', params: {feedbackId: obj.id}})
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
