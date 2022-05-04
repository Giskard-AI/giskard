<template>
  <div>
  <div class="d-flex justify-end">
    <v-btn text @click="loadModelPickles()" color="secondary">Reload<v-icon right>refresh</v-icon></v-btn>
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
          <div>{{ m.python_version }}</div>
        </v-col>
        <v-col cols="1">
          <div>{{ formatSizeForDisplay(m.size) }}</div>
        </v-col>
        <v-col cols="3">
          <div>{{ new Date(m.creation_date).toLocaleString() }}</div>
        </v-col>
        <v-col cols="3">
          <div>
            <v-btn small tile color="primary" 
            @click="showInspectDialog = true; modelToInspect = m.id">
              <v-icon dense left>policy</v-icon>
              Inspect
            </v-btn>
            <v-tooltip bottom>
              <template v-slot:activator="{ on, attrs }">
                <v-btn icon color="info" @click="downloadModelPickle(m.id, m.name)" v-bind="attrs" v-on="on">
                  <v-icon>download</v-icon>
                </v-btn>
                </template>
              <span>Download</span>
            </v-tooltip>
            <v-tooltip bottom>
              <template v-slot:activator="{ on, attrs }">
                <v-btn icon color="accent" v-if="isProjectOwnerOrAdmin" @click="deleteModelPickle(m.id, m.name)" v-bind="attrs" v-on="on">
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
      <InspectorLauncher :projectId="projectId" :modelId="modelToInspect"
        @cancel="cancelLaunchInspector()" />
    </v-dialog>

  </v-container>
  <v-container v-else class="font-weight-light font-italic secondary--text">
    No models uploaded yet.
  </v-container>
  </div>
</template>

<script lang="ts">
import { Component, Vue, Prop, Watch } from 'vue-property-decorator';
import { api } from '@/api';
import { dialogDownloadFile, performApiActionWithNotif } from '@/api-commons';
import { readToken } from '@/store/main/getters';
import { formatSizeForDisplay } from '@/utils';
import { commitAddNotification } from '@/store/main/mutations';
import InspectorLauncher from './InspectorLauncher.vue';
import { ModelDTO } from '@/generated-sources';

@Component({
  components: { InspectorLauncher }
})
export default class Models extends Vue {
	@Prop({type: Number, required: true}) projectId!: number;
	@Prop({type: Boolean, required: true, default: false}) isProjectOwnerOrAdmin!: boolean;

	models: ModelDTO[] = [];
  showInspectDialog = false;
  modelToInspect: number | null = null;

	activated() {
		this.loadModelPickles()
	}

	private async loadModelPickles() {
		const response = await api.getProjectModels(readToken(this.$store), this.projectId)
    this.models = response.data.sort((a, b) => new Date(a.creation_date) < new Date(b.creation_date) ? 1 : -1);
	}

	public formatSizeForDisplay = (size: number) => formatSizeForDisplay(size);

	public async deleteModelPickle(id: number, fileName: string) {
    if (await this.$dialog.confirm({
      text: `Are you sure you want to delete model <strong>${fileName}</strong>?`,
      title: 'Delete model'
    })) {
      performApiActionWithNotif(this.$store,
          () => api.deleteDatasetFile(readToken(this.$store), id),
          this.loadModelPickles)
    }
  }

	public async downloadModelPickle(id: number, fileName: string) {
		try {
			const response = await api.downloadModelFile(readToken(this.$store), id)
			dialogDownloadFile(response, fileName);
		} catch (error) {
			commitAddNotification(this.$store, { content: error.response.statusText, color: 'error' });
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
