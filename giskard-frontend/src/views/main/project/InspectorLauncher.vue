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
              :value="n.id"
          ></v-radio>
        </v-radio-group>
      </div>
      <div v-else>No dataset uploaded yet on this project.</div>
    </v-card-text>
    <!--          <v-card-actions class="justify-end">-->
    <!--            <v-btn text @click="reset()"> Cancel </v-btn>-->
    <!--            <v-btn-->
    <!--              color="primary"-->
    <!--              @click="-->
    <!--                step++;-->
    <!--                loadDatasetFeatures();-->
    <!--              "-->
    <!--              :disabled="!datasetSelected"-->
    <!--            >-->
    <!--              Continue-->
    <!--            </v-btn>-->
    <!--          </v-card-actions>-->
    <v-card-actions>
      <!--            <v-btn text @click="step&#45;&#45;">Back</v-btn>-->
      <v-btn text @click="reset()"> Cancel </v-btn>
      <v-spacer></v-spacer>
      <!--            <v-btn text @click="targetFeature = null">Clear</v-btn>-->
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
import { Component, Emit, Prop, Vue } from 'vue-property-decorator';
import OverlayLoader from '@/components/OverlayLoader.vue';
import { readToken } from '@/store/main/getters';
import { commitAddNotification } from '@/store/main/mutations';
import { api } from '@/api';
import {FileDTO, ModelDTO, ModelMetadataDTO} from '@/generated-sources';

@Component({
  components: { OverlayLoader }
})
export default class InspectorLauncher extends Vue {
  @Prop({ required: true }) projectId!: number;
  @Prop({ required: true }) model!: ModelDTO;
  loading = false;
  step = 1;
  datasets: FileDTO[] = [];
  datasetSelected: number | null = null;
  datasetFeatures: string[] = [];
  errorLoadingFeatures: string | null = null;

  public async mounted() {
    this.loadDatasets();
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
    const response = await api.getProjectDatasets(
      readToken(this.$store),
      this.projectId
    );
    this.datasets = response.data.sort((a, b) =>
      new Date(a.createdDate) < new Date(b.createdDate) ? 1 : -1
    );
    this.loading = false;
  }

  public async loadDatasetFeatures() {
    if (this.datasetSelected) {
      try {
        this.loading = true;
        const response = await api.peakDataFile(
          readToken(this.$store),
          this.datasetSelected
        );
        const headers = JSON.parse(response.data)['schema']['fields'];
        this.datasetFeatures = headers
          .map((e) => e['name'].trim())
          .filter((e) => e != 'index');
      } catch (error) {
        commitAddNotification(this.$store, {
          content: error.response.data.detail,
          color: 'error'
        });
        this.errorLoadingFeatures = error.response.data.detail;
      } finally {
        this.loading = false;
      }
    }
  }

  public async launchInspector() {
    const inspection=await api.prepareInspection(readToken(this.$store), this.model.id.toString(), this.datasetSelected?.toString()!, this.model.target!);
    const query = {
      model: this.model.id.toString(),
      dataset: this.datasetSelected?.toString(),
      target: this.model.target,
      inspection:inspection.data.id
    };
    this.$router.push({ name: 'project-inspector', query});
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
