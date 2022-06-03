<template>
  <div>
    <OverlayLoader v-show="loading" />
    <v-container>
      <p v-if="textFeatureNames.length == 0" class="text-center">None</p>
      <div v-else>
        <v-row>
          <v-col cols="5" v-if='textFeatureNames.length>1'>
            <p class="caption secondary--text text--lighten-2 my-1">Feature</p>
            <v-select
              dense
              solo
              v-model="selectedFeature"
              :items="textFeatureNames"
            ></v-select>
          </v-col>
          <v-col cols="5">
            <p class="caption secondary--text text--lighten-2 my-1">
              Classification Label
            </p>
            <v-select
              dense
              solo
              v-model="selectedLabel"
              :items="classificationLabels"
            ></v-select>
          </v-col>
          <v-col cols="2" class="d-flex align-center">
            <v-btn
              tile
              small
              color="primary"
              @click="getExplanation"
              :disabled="submitted"
            >
              <v-icon left>play_arrow</v-icon>Run
            </v-btn>
          </v-col>
        </v-row>
        <div v-if="result">
          <p class="caption text-center">Word contribution (LIME values)</p>
          <p class="result-paragraph" v-html="result[selectedLabel]"></p>
        </div>
      </div>
      <p v-if="errorMsg" class="error--text">
        {{ errorMsg }}
      </p>
    </v-container>
  </div>
</template>

<script lang="ts">
import { Component, Vue, Prop, Watch } from "vue-property-decorator";
import OverlayLoader from "@/components/OverlayLoader.vue";
import { api } from "@/api";
import { readToken } from "@/store/main/getters";

@Component({
  components: { OverlayLoader },
})
export default class TextExplanation extends Vue {
  @Prop({ required: true }) modelId!: number;
  @Prop({ required: true }) datasetId!: number;
  @Prop({ required: true }) textFeatureNames!: string[];
  @Prop({ required: true }) classificationLabels!: string[];
  @Prop({ default: {} }) inputData!: object;
  @Prop() classificationResult!: string;

  loading: boolean = false;
  originalInputData = {}; // used for the watcher to trigger the explanation call
  selectedFeature = "";
  selectedLabel = this.classificationResult || this.classificationLabels[0];
  errorMsg: string = "";
  result: string = "";
  submitted = false;

   mounted(){
    this.selectedFeature= this.textFeatureNames[0];
  }

  @Watch("classificationResult")
  setSelectedLabel() {
    if (
      this.classificationResult &&
      this.classificationLabels.indexOf(this.classificationResult) > 0
    ) {
      this.selectedLabel = this.classificationResult;
    } else this.selectedLabel = this.classificationLabels[0];
  }

  public async getExplanation() {
    if (this.selectedFeature && this.inputData[this.selectedFeature].length) {
      try {
        this.loading = true;
        this.errorMsg = "";
        const response = await api.explainText(
          this.modelId,
          this.inputData,
          this.selectedFeature
        );
        this.result = response.data;
        this.submitted = true;
      } catch (error) {
        this.result = "";
        this.errorMsg = error.response.data.detail;
      } finally {
        this.loading = false;
      }
    } else {
      // reset
      this.errorMsg = "";
      this.result = "";
    }
  }
  @Watch("selectedFeature")
  @Watch("inputData", { deep: true })
  reset() {
    this.submitted = false;
    this.result = "";
    this.errorMsg = "";
  }
}
</script>

<style scoped>
p.result-paragraph {
  max-height: 300px;
  overflow-y: auto;
  padding-top: 6px;
}
</style>
