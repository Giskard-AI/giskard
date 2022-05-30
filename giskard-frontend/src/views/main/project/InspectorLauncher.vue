<template>
  <v-card flat>
    <v-card-title>
      Select dataset
    </v-card-title>
    <OverlayLoader v-show="loading" />
    <v-card-text class="scrollable-with-limits">
      <div v-if="datasets.length > 0">
        <v-radio-group v-model="datasetSelected">
          <v-radio
              v-for="n in datasets"
              :key="n.id"
              :label="n.name"
              :value="n"
          ></v-radio>
        </v-radio-group>
      </div>
      <div v-else>No dataset uploaded yet on this project.</div>
    </v-card-text>
    <v-card-actions>
      <v-btn text @click="reset()"> Cancel </v-btn>
      <v-spacer></v-spacer>
      <v-btn
          color="primary"
          @click="launchInspector()"
          :disabled="errorLoadingFeatures"
      >
        Inspect
      </v-btn>
    </v-card-actions>
  </v-card>

</template>

<script lang="ts">
import {Component, Emit, Prop, Vue} from 'vue-property-decorator';
import OverlayLoader from '@/components/OverlayLoader.vue';
import {readToken} from '@/store/main/getters';
import {commitAddNotification} from '@/store/main/mutations';
import {api} from '@/api';
import {DatasetDTO, ModelDTO} from '@/generated-sources';

@Component({
  components: { OverlayLoader }
})
export default class InspectorLauncher extends Vue {
  @Prop({ required: true }) projectId!: number;
  @Prop({ required: true }) model!: ModelDTO;
  loading = false;
  step = 1;
  datasets: DatasetDTO[] = [];
  datasetSelected: DatasetDTO | null = null;
  datasetFeatures: string[] = [];
  errorLoadingFeatures: string | null = null;

  public async mounted() {
    await this.loadDatasets();
  }

  @Emit('cancel')
  public reset() {
    this.step = 1;
    this.datasetSelected = null;
    this.datasetFeatures = [];
    this.errorLoadingFeatures = null;
  }

  public async loadDatasets() {
    this.loading = true;
    const response = await api.getProjectDatasets(this.projectId);
    this.datasets = response.sort((a, b) =>
      new Date(a.createdDate) < new Date(b.createdDate) ? 1 : -1
    );
    this.loading = false;
  }

  public async launchInspector() {
    const inspection = await api.prepareInspection({datasetId: this.datasetSelected!.id, modelId: this.model.id});
    await this.$router.push({ name: 'project-inspector', params: {inspectionId: inspection.id.toString()}});
    this.reset();
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
