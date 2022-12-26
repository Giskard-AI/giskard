<template>
  <v-card flat>
    <v-card-title>
      Select dataset
    </v-card-title>
    <OverlayLoader :show="loading"/>
    <v-card-text class="scrollable-with-limits">
      <div v-if="datasets.length > 0">
        <v-radio-group v-model="datasetSelected">
          <v-radio
              v-for="n in datasets"
              :key="n.id"
              :label="n.name || n.id"
              :value="n"
          ></v-radio>
        </v-radio-group>
      </div>
      <div v-else>No dataset uploaded yet on this project.</div>
    </v-card-text>
    <v-card-actions>
      <v-btn text @click="reset()"> Cancel</v-btn>
      <v-spacer></v-spacer>
      <v-btn
          color="primary"
          @click="launchInspector()"
          :disabled="creatingInspection"
          :loading='creatingInspection'
      >
        Inspect
      </v-btn>
    </v-card-actions>
  </v-card>

</template>

<script lang="ts">
import {Component, Emit, Prop, Vue} from 'vue-property-decorator';
import OverlayLoader from '@/components/OverlayLoader.vue';
import {api} from '@/api';
import {DatasetDTO, ModelDTO} from '@/generated-sources';
import mixpanel from "mixpanel-browser";

@Component({
  components: {OverlayLoader}
})
export default class InspectorLauncher extends Vue {
  @Prop({required: true}) projectId!: number;
  @Prop({required: true}) model!: ModelDTO;
  loading = false;
  step = 1;
  datasets: DatasetDTO[] = [];
  datasetSelected: DatasetDTO | null = null;
  datasetFeatures: string[] = [];
  creatingInspection = false;

  public async mounted() {
    await this.loadDatasets();
  }

  @Emit('cancel')
  public reset() {
    this.step = 1;
    this.datasetSelected = null;
    this.datasetFeatures = [];
  }

  public async loadDatasets() {
    this.loading = true;
    this.datasets = await api.getProjectDatasets(this.projectId);
    this.datasets.sort((a, b) =>
        new Date(a.createdDate) < new Date(b.createdDate) ? 1 : -1
    );
    this.loading = false;
  }

  public async launchInspector() {
    mixpanel.track('Create inspection', {datasetId: this.datasetSelected!.id, modelId: this.model.id});
    try {
      this.creatingInspection = true;
      const inspection = await api.prepareInspection({datasetId: this.datasetSelected!.id, modelId: this.model.id});
      await this.$router.push({name: 'project-inspector', params: {inspectionId: inspection.id.toString()}});
      this.reset();
    } finally {
      this.creatingInspection = false;
    }
  }
}
</script>

<style scoped>
.scrollable-with-limits {
  min-height: 140px;
  max-height: 50vh;
  overflow-y: auto;
}
</style>
