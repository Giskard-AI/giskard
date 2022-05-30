<template>
  <div>
    <div class="d-flex justify-end">
      <v-btn text @click="loadModelPickles()" color="secondary">Reload
        <v-icon right>refresh</v-icon>
      </v-btn>
    </div>
    <v-container v-if="models.length > 0">
      <v-card flat>
        <v-row class="px-2 py-1 caption secondary--text text--lighten-3">
          <v-col cols="4">Name</v-col>
          <v-col cols="1">Python</v-col>
          <v-col cols="1">Size</v-col>
          <v-col cols="3">Uploaded on</v-col>
          <v-col cols="3">Actions</v-col>
        </v-row>
      </v-card>
      <v-card outlined tile class="grey lighten-5" v-for="m in models" :key="m.id">
        <v-row class="px-2 py-1 align-center">
          <v-col cols="4">
            <div class="secondary--text font-weight-bold">
              {{ m.name }}
            </div>
          </v-col>
          <v-col cols="1">
            <div>{{ m.languageVersion }}</div>
          </v-col>
          <v-col cols="1">
            <div>{{ m.size | fileSize }}</div>
          </v-col>
          <v-col cols="3">
            <div>{{ m.createdDate | date }}</div>
          </v-col>
          <v-col cols="3">
            <div>
              <v-btn small tile color="primary"
                     @click="showInspectDialog = true; modelToInspect = m">
                <v-icon dense left>policy</v-icon>
                Inspect
              </v-btn>
              <v-tooltip bottom>
                <template v-slot:activator="{ on, attrs }">
                  <v-btn icon color="info" @click="downloadModelPickle(m.id)" v-bind="attrs" v-on="on">
                    <v-icon>download</v-icon>
                  </v-btn>
                </template>
                <span>Download</span>
              </v-tooltip>
              <v-tooltip bottom>
                <template v-slot:activator="{ on, attrs }">
                  <v-btn icon color="accent" v-if="isProjectOwnerOrAdmin" @click="deleteModelPickle(m.id, m.name)"
                         v-bind="attrs" v-on="on">
                    <v-icon>delete</v-icon>
                  </v-btn>
                </template>
                <span>Delete</span>
              </v-tooltip>
            </div>
          </v-col>
        </v-row>
        <v-divider></v-divider>
      </v-card>

      <!-- Dialog for launching model inspection -->
      <v-dialog persistent max-width="600" v-model="showInspectDialog" class="inspector-launcher-container">
        <InspectorLauncher :projectId="projectId" :model="modelToInspect"
                           @cancel="cancelLaunchInspector()"/>
      </v-dialog>

    </v-container>
    <v-container v-else class="font-weight-light font-italic secondary--text">
      No models uploaded yet.
    </v-container>
  </div>
</template>

<script lang="ts">
import {Component, Prop, Vue} from 'vue-property-decorator';
import {api} from '@/api';
import {performApiActionWithNotif} from '@/api-commons';
import {readToken} from '@/store/main/getters';
import {commitAddNotification} from '@/store/main/mutations';
import InspectorLauncher from './InspectorLauncher.vue';
import {ModelDTO} from '@/generated-sources';

@Component({
  components: {InspectorLauncher}
})
export default class Models extends Vue {
  @Prop({type: Number, required: true}) projectId!: number;
  @Prop({type: Boolean, required: true, default: false}) isProjectOwnerOrAdmin!: boolean;

  models: ModelDTO[] = [];
  showInspectDialog = false;
  modelToInspect: ModelDTO | null = null;

  activated() {
    this.loadModelPickles()
  }

  private async loadModelPickles() {
    const response = await api.getProjectModels(this.projectId)
    this.models = response.sort((a, b) => new Date(a.createdDate) < new Date(b.createdDate) ? 1 : -1);
  }

  public async deleteModelPickle(id: number, fileName: string) {
    if (await this.$dialog.confirm({
      text: `Are you sure you want to delete model <strong>${fileName}</strong>?`,
      title: 'Delete model'
    })) {
      await performApiActionWithNotif(this.$store,
          () => api.deleteModelFiles(id),
          this.loadModelPickles)
    }
  }

  public downloadModelPickle(id: number) {
    try {
      api.downloadModelFile(id)
    } catch (error) {
      commitAddNotification(this.$store, {content: error.response.statusText, color: 'error'});
    }
  }

  public cancelLaunchInspector() {
    this.showInspectDialog = false;
  }

}
</script>

<style>
div.v-dialog {
  overflow-y: hidden;
}
</style>
