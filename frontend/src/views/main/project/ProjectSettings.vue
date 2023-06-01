<template>
  <v-container fluid class="font-weight-light mt-3">
    <v-row>
      <v-col cols="9">
        <v-card height="100%">
          <v-card-title class="font-weight-light secondary--text">
            Properties
          </v-card-title>
          <v-card-text class="container">
            <v-row>
              <v-col cols="6">
                <v-simple-table class="properties-table-c1">
                  <tr>
                    <td>Project Description:</td>
                    <td>{{ project.description }}</td>
                  </tr>
                  <tr>
                    <td>Project Unique Key:</td>
                    <td>{{ project.key }}</td>
                  </tr>
                  <tr>
                    <td>Project ID:</td>
                    <td>{{ project.id }}</td>
                  </tr>
                </v-simple-table>
              </v-col>
              <v-col cols="6">
                <v-simple-table class="properties-table-c2">
                  <tr>
                    <td>Created by:</td>
                    <td>{{ getUserFullDisplayName(project.owner) }}</td>
                  </tr>
                  <tr>
                    <td>Created at:</td>
                    <td>{{ project.createdDate | date }}</td>
                  </tr>
                  <tr>
                    <td>ML Worker:</td>
                    <td>{{ project.mlWorkerType.toLowerCase() }}</td>
                  </tr>
                </v-simple-table>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="3">
        <v-card height="100%">
          <v-card-title class="font-weight-light secondary--text">
            Guest Users
          </v-card-title>
          <v-card-text>
            <div class="px-2">
              <table v-if="project.guests.length">
                <tr v-for="p in project.guests" :key="p.user_id">
                  <td class="caption pr-4">{{ getUserFullDisplayName(p) }}</td>
                  <td v-if="isProjectOwnerOrAdmin">
                    <v-btn icon small color="accent" @click="cancelUserInvitation(p)">
                      <v-icon small>person_remove</v-icon>
                    </v-btn>
                  </td>
                </tr>
              </table>
              <p v-else class="caption">None</p>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-divider class="my-6"></v-divider>
    <div class="mb-6 d-flex">
      <!-- <h1 class="headline">Data Objects</h1> -->
      <div class="d-flex justify-end align-center flex-grow-1">
        <v-btn tile small color="primaryLight" class="mx-2 primaryLighBtn" href="https://docs.giskard.ai/start/guides/upload-your-model" target="_blank">
          Upload with API
        </v-btn>
        <v-btn text @click="reloadDataObjects()" color="secondary">Reload
          <v-icon right>refresh</v-icon>
        </v-btn>
      </div>
    </div>

    <v-row>
      <v-col cols="6">
        <v-card height="100%" outlined>
          <v-card-title class="font-weight-light secondary--text">
            <v-icon left class="pb-1">stacked_bar_chart</v-icon>
            Datasets
          </v-card-title>
          <v-card-text>
            <Datasets ref="datasetsComponentRef" :projectId="projectId" :isProjectOwnerOrAdmin="isProjectOwnerOrAdmin"></Datasets>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="6">
        <v-card height="100%" outlined>
          <v-card-title class="font-weight-light secondary--text">
            <v-icon left class="pb-1">settings_suggest</v-icon>
            Models
          </v-card-title>
          <v-card-text>
            <Models ref="modelsComponentRef" :projectId="projectId" :isProjectOwnerOrAdmin="isProjectOwnerOrAdmin"></Models>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
// import { Component, Prop, Vue } from 'vue-property-decorator';
import { getUserFullDisplayName } from '@/utils';
import Models from '@/views/main/project/Models.vue';
import Datasets from '@/views/main/project/Datasets.vue';
// import FeedbackList from '@/views/main/project/FeedbackList.vue';
import { IUserProfileMinimal } from '@/interfaces';
import mixpanel from "mixpanel-browser";
import { useProjectStore } from "@/stores/project";
import { computed, ref } from 'vue';
import { mode } from 'crypto-js';

interface Props {
  projectId: number;
  isProjectOwnerOrAdmin: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  isProjectOwnerOrAdmin: false
});

const datasetsComponentRef = ref<any>(null);
const modelsComponentRef = ref<any>(null);

const project = computed(() => useProjectStore().project(props.projectId))


function reloadDataObjects() {
  datasetsComponentRef.value.loadDatasets();
  modelsComponentRef.value.loadModelPickles();
}

async function cancelUserInvitation(user: IUserProfileMinimal) {
  // const confirm = await this.$dialog.confirm({
  //   text: `Are you sure you want to cancel invitation of user <strong>${user.user_id}</strong>?`,
  //   title: 'Cancel user invitation'
  // });
  // if (project && confirm) {

  if (project) {
    try {
      mixpanel.track('Cancel user invitation to project', { projectId: project.id, userId: user.id });
      await useProjectStore().uninviteUserFromProject({ projectId: project.id, userId: user.id })
    } catch (e) {
      console.error(e)
    }
  }
}

</script>

<!-- <script lang="ts">
import { Component, Prop, Vue } from 'vue-property-decorator';
import { getUserFullDisplayName } from '@/utils';
import Models from '@/views/main/project/Models.vue';
import Datasets from '@/views/main/project/Datasets.vue';
import FeedbackList from '@/views/main/project/FeedbackList.vue';
import { IUserProfileMinimal } from '@/interfaces';
import mixpanel from "mixpanel-browser";
import { useProjectStore } from "@/stores/project";

@Component({
  components: {
    Models, Datasets, FeedbackList
  }
})
export default class ProjectSettings extends Vue {

  @Prop({ required: true }) projectId!: number;
  @Prop({ type: Boolean, required: true, default: false }) isProjectOwnerOrAdmin!: boolean;

  get project() {
    return useProjectStore().project(this.projectId);
  }

  private getUserFullDisplayName = getUserFullDisplayName

  public async cancelUserInvitation(user: IUserProfileMinimal) {
    const confirm = await this.$dialog.confirm({
      text: `Are you sure you want to cancel invitation of user <strong>${user.user_id}</strong>?`,
      title: 'Cancel user invitation'
    });
    if (this.project && confirm) {
      try {
        mixpanel.track('Cancel user invitation to project', { projectId: this.project.id, userId: user.id });
        await useProjectStore().uninviteUserFromProject({ projectId: this.project.id, userId: user.id })
      } catch (e) {
        console.error(e)
      }
    }
  }
}
</script> -->

<style scoped lang="scss">
.properties-table-c1 {
  tr {
    td:first-child {
      width: 150px;
    }

    td:nth-child(2) {
      font-weight: bold;
    }
  }
}

.properties-table-c2 {
  tr {
    td:first-child {
      width: 100px;
    }

    td:nth-child(2) {
      font-weight: bold;
    }
  }
}
</style>
