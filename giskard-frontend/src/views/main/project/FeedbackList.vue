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
				:group-by="groupByFeature ? 'feature_name': null"
        :items="feedbacks"
        :headers="tableHeaders"
        :search="search"
        @click:row="openFeedback"
      >
				<!-- eslint-disable-next-line vue/valid-v-slot -->
				<template v-slot:item.created_on="{ item }">
					<span>{{ new Date(item.created_on).toLocaleString() }}</span>
				</template>
				<!-- eslint-disable-next-line vue/valid-v-slot -->
				<template v-slot:item.feature_value="{ item }">
					<span>{{ (item.feature_value && item.feature_value.length > 140) ? item.feature_value.slice(0, 140) + "..." : item.feature_value }}</span>
				</template>
      </v-data-table>
    </v-container>
    <v-dialog width="90vw" v-model="openFeedbackDetail" @click:outside="$router.push({name: 'project-feedbacks'})">
      <router-view/>
    </v-dialog>
  </div>
</template>

<script lang="ts">
import { Component, Vue, Prop, Watch } from "vue-property-decorator";
import { api } from "@/api";
import { readToken } from "@/store/main/getters";
import { IFeedbackForList } from "@/interfaces";
import { commitAddNotification } from '@/store/main/mutations';
import FeedbackDetail from './FeedbackDetail.vue';

@Component({
  components: {FeedbackDetail}
})
export default class FeedbackList extends Vue {
  @Prop({ required: true }) projectId!: number;

  feedbacks: IFeedbackForList[] = [];
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
        value: "model_name",
        align: "left",
        filter: (value) => !this.modelFilter ? true : value == this.modelFilter,
      },
      {
        text: "Dataset",
        sortable: true,
        value: "dataset_name",
        align: "left",
        filter: (value) => !this.datasetFilter ? true : value == this.datasetFilter,
      },
      {
        text: "User ID",
        sortable: true,
        value: "user_id",
        align: "left",
      },
      {
				text: 'On',
				value: 'created_on',
				sortable: true,
				filterable: false,
				align: 'left'
      },
      {
        text: "Type",
        sortable: true,
        value: "feedback_type",
        align: "left",
        filter: (value) => !this.typeFilter ? true : value == this.typeFilter,
      },
      {
        text: "Feature name",
        sortable: true,
        value: "feature_name",
        align: "left",
      },
      {
        text: "Feature value",
        sortable: true,
        value: "feature_value",
        align: "left",
      },
      {
        text: "Choice",
        sortable: true,
        value: "feedback_choice",
        align: "left",
      },
      {
        text: "Message",
        sortable: true,
        value: "feedback_message",
        align: "left",
      },
    ];
  }

  get existingModels() {
    return this.feedbacks.map((e) => e.model_name);
  }

  get existingDatasets() {
    return this.feedbacks.map((e) => e.dataset_name);
  }

  get existingTypes() {
    return this.feedbacks.map((e) => e.feedback_type);
  }

  public async fetchFeedbacks() {
		try {
			const response = await api.getProjectFeedbacks(readToken(this.$store), this.projectId);
			this.feedbacks = response.data;
		} catch (error) {
			commitAddNotification(this.$store, { content: error.response.data.detail, color: 'error' });
		}
  }

  public async openFeedback(obj) {
    this.$router.push({name: 'feedback-detail', params: {feedbackId: obj.id}})
  }

}
</script>

<style scoped>
div.v-input.flex-1 {
	flex: 1  /* ugly, but no other idea */
}

.v-data-table >>> tbody > tr {
  cursor: pointer;
}
</style>
