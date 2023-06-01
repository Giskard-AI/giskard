<template>
  <div class="vertical-container">
    <v-container class="mt-2 mb-0" v-if="isProjectOwnerOrAdmin">
      <div class="d-flex justify-end align-center">
        <v-btn tile small class="mx-2" href="https://docs.giskard.ai/start/guides/upload-your-model" target="_blank">
          Upload with API
        </v-btn>
        <v-btn text @click="loadDatasets()" color="secondary">Reload
          <v-icon right>refresh</v-icon>
        </v-btn>
      </div>
    </v-container>
    <v-container v-if="files.length > 0">
      <v-expansion-panels>
        <v-row dense no-gutters class="mr-12 ml-2 caption secondary--text text--lighten-3 pb-2">
          <v-col cols="4">Name</v-col>
          <v-col cols="1">Size</v-col>
          <v-col cols="3">Uploaded on</v-col>
          <v-col cols="2">Target</v-col>
          <v-col cols="1">Id</v-col>
          <v-col>Actions</v-col>
        </v-row>

        <v-expansion-panel v-for="f in files" :key="f.id">
          <v-expansion-panel-header @click="peakDataFile(f.id)" class="py-1 pl-2">
            <v-row dense no-gutters align="center">
              <v-col cols="4" class="font-weight-bold">{{ f.name || f.id }}</v-col>
              <v-col cols="1">{{ f.originalSizeBytes | fileSize }}</v-col>
              <v-col cols="3">{{ f.createdDate | date }}</v-col>
              <v-col cols="2">{{ f.target }}</v-col>
              <v-col cols="1" class="id-container" :title="f.id"> {{ f.id }}</v-col>
              <v-col>
                <span>
              <v-tooltip bottom dense>
                <template v-slot:activator="{ on, attrs }">
                  <v-btn icon color="info" @click.stop="downloadDataFile(f.id)" v-bind="attrs" v-on="on">
                    <v-icon>download</v-icon>
                  </v-btn>
                  </template>
                <span>Download</span>
              </v-tooltip>
              <v-tooltip bottom dense>
                <template v-slot:activator="{ on, attrs }">
                    <v-btn icon color="accent" v-if="isProjectOwnerOrAdmin"
                           @click.stop="deleteDataFile(f.id, f.name)"
                           v-bind="attrs" v-on="on">
                      <v-icon>delete</v-icon>
                    </v-btn>
                  </template>
                <span>Delete</span>
              </v-tooltip>
            </span>
              </v-col>
            </v-row>

          </v-expansion-panel-header>
          <v-expansion-panel-content>
            <v-data-table :headers="filePreviewHeader" :items="filePreviewData"
                          dense :hide-default-footer="true"
                          v-if="filePreviewHeader.length > 0 && filePreviewData.length > 0">
            </v-data-table>
            <div class="caption" v-else>Could not properly load data</div>
          </v-expansion-panel-content>
        </v-expansion-panel>
      </v-expansion-panels>
    </v-container>
    <v-container v-else class="font-weight-light font-italic secondary--text">
      No files uploaded yet.
    </v-container>
  </div>
</template>

<script lang="ts">
import {Component, Prop, Vue} from "vue-property-decorator";
import {api} from '@/api';
import {commitAddNotification} from '@/store/main/mutations';
import {DatasetDTO} from '@/generated-sources';
import mixpanel from "mixpanel-browser";
import DeleteModal from "@/views/main/project/modals/DeleteModal.vue";

const GISKARD_INDEX_COLUMN_NAME = '_GISKARD_INDEX_';


@Component
export default class Datasets extends Vue {
  @Prop({type: Number, required: true}) projectId!: number;
  @Prop({type: Boolean, default: false}) isProjectOwnerOrAdmin!: boolean;

  public files: DatasetDTO[] = [];
  public fileData = null;
  public lastVisitedFileId;
  public filePreviewHeader: { text: string, value: string, sortable: boolean }[] = [];
  public filePreviewData: any[] = [];

  activated() {
    this.loadDatasets()
  }

  private async loadDatasets() {
    this.files = await api.getProjectDatasets(this.projectId)
    this.files.sort((a, b) => new Date(a.createdDate) < new Date(b.createdDate) ? 1 : -1);
  }

  public async deleteDataFile(id: string, fileName: string) {
    mixpanel.track('Delete dataset', {id});
    if (await this.$dialog.showAndWait(DeleteModal, {
      width: 600,
      id: id,
      fileName: fileName,
      type: "dataset",
      scrollable: true
    })) {
      let messageDTO = await api.deleteDatasetFile(id);
      commitAddNotification(this.$store, {content: messageDTO.message});
      await this.loadDatasets();
    }
  }

  public downloadDataFile(id: string) {
    mixpanel.track('Download dataset file', {id});
    api.downloadDataFile(id)
  }

  public async peakDataFile(id: string) {
    if (this.lastVisitedFileId != id) {
      this.lastVisitedFileId = id; // this is a trick to avoid recalling the api every time one panel is opened/closed
      try {
        const response = await api.peekDataFile(id)
        const headers = Object.keys(response[0])
        this.filePreviewHeader = headers.filter(e => e != GISKARD_INDEX_COLUMN_NAME).map(e => {
          return {text: e.trim(), value: e, sortable: false}
        });
        if (headers.includes(GISKARD_INDEX_COLUMN_NAME)) {
          this.filePreviewHeader = [{
            text: '#',
            value: GISKARD_INDEX_COLUMN_NAME,
            sortable: false
          }].concat(this.filePreviewHeader);
        }
        this.filePreviewData = response
      } catch (error) {
        commitAddNotification(this.$store, {content: error.response.statusText, color: 'error'});
        this.filePreviewHeader = [];
        this.filePreviewData = [];
      }
    }
  }
}
</script>

<style lang="scss" scoped>
::v-deep .v-data-table__wrapper .v-data-table-header [role='columnheader'] {
  user-select: auto;
}

.file-xl {
  border-left: 4px solid #4CAF50
}

.file-csv {
  border-left: 4px solid #03A9F4
}

div.v-input {
  width: 400px;
}

.id-container {
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
