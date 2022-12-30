<template>
  <v-container fluid class="font-weight-light">
    <p class="caption">
      <v-simple-table class="info-table">
        <tr>
          <td>Project Unique Key</td>
          <td>{{ project.key }}</td>
        </tr>
        <tr>
          <td>Project Id</td>
          <td>{{ project.id }}</td>
        </tr>
        <tr>
          <td>Created by</td>
          <td>{{ getUserFullDisplayName(project.owner) }}</td>
        </tr>
        <tr>
          <td>On</td>
          <td>{{ project.createdDate | date }}</td>
        </tr>
        <tr>
          <td>ML Worker</td>
          <td>{{ project.mlWorkerType.toLowerCase() }}</td>
        </tr>
      </v-simple-table>
    </p>
    <p v-show="project.description">{{ project.description }}</p>
    <v-divider class="my-4"></v-divider>
    <div class="subtitle-1">
      Guest Users
    </div>
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
  </v-container>
</template>

<script lang="ts">
import {Component, Prop, Vue} from 'vue-property-decorator';
import {readProject} from '@/store/main/getters';
import {dispatchUninviteUser} from '@/store/main/actions';
import {getUserFullDisplayName} from '@/utils';
import Models from '@/views/main/project/Models.vue';
import Datasets from '@/views/main/project/Datasets.vue';
import FeedbackList from '@/views/main/project/FeedbackList.vue';
import {IUserProfileMinimal} from '@/interfaces';
import mixpanel from "mixpanel-browser";

@Component({
  components: {
    Models, Datasets, FeedbackList
  }
})
export default class ProjectOverview extends Vue {

  @Prop({required: true}) projectId!: number;
  @Prop({type: Boolean, required: true, default: false}) isProjectOwnerOrAdmin!: boolean;
  get project() {
    return readProject(this.$store)(this.projectId)
  }

  private getUserFullDisplayName = getUserFullDisplayName

  public async cancelUserInvitation(user: IUserProfileMinimal) {
    const confirm = await this.$dialog.confirm({
      text: `Are you sure you want to cancel invitation of user <strong>${user.user_id}</strong>?`,
      title: 'Cancel user invitation'
    });
    if (this.project && confirm) {
      try {
        mixpanel.track('Cancel user invitation to project', {projectId: this.project.id, userId: user.id});
        await dispatchUninviteUser(this.$store, {projectId: this.project.id, userId: user.id})
      } catch (e) {
        console.error(e)
      }
    }
  }
}
</script>

<style scoped lang="scss">
.info-table {
  tr {
    td:first-child {
      width: 150px;
    }

    td:nth-child(2) {
      font-weight: bold;
    }
  }
}
</style>
