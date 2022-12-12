<template>
  <div>
    <OverlayLoader :show="loading" absolute solid/>
    <v-container>
      <p v-if="textFeatureNames.length === 0" class="text-center">None</p>
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
            <v-autocomplete
                dense
                solo
                v-model="selectedLabel"
                :items="classificationLabels"
            ></v-autocomplete>
          </v-col>
          <v-col cols="2" class="d-flex align-center">
            <v-btn
                tile
                small
                color="primary"
                @click="getExplanation"
                :disabled="submitted"
            >
              <v-icon left>play_arrow</v-icon>
              Run
            </v-btn>
          </v-col>
        </v-row>
        <div v-if="result != null">
          <p class="caption text-center">Word contribution (LIME values)</p>
          <p class="result-paragraph" v-if="(Object.keys(result.explanations).length !== 0)"> <TextExplanationParagraph :weights="result.explanations[selectedLabel]" :max_weight="max_weight"></TextExplanationParagraph> </p>
        </div>
      </div>
      <p v-if="errorMsg" class="error--text">
        {{ errorMsg }}
      </p>
    </v-container>
  </div>
</template>

<script lang="ts" setup>
import {ref, watch} from "vue";
import mixpanel from "mixpanel-browser";
import { ExplainTextResponseDTO } from '@/generated-sources'
import TextExplanationParagraph from './TextExplanationParagraph.vue';
import {api} from "@/api";
import OverlayLoader from "@/components/OverlayLoader.vue";
import { max_value } from "vee-validate/dist/rules";

interface Props {
  modelId: number,
  datasetId: number,
  textFeatureNames: string[],
  classificationLabels: string[]
  inputData?: object,
  classificationResult: string
}

const props = withDefaults(defineProps<Props>(), {
  inputData: () => ({})
});

const loading = ref<boolean>(false);
const selectedFeature = ref<string>(props.textFeatureNames[0]);
const selectedLabel = ref<string>(props.classificationResult || props.classificationLabels[0]);
const errorMsg = ref<string>("");
const result = ref<ExplainTextResponseDTO | null>(null);
const submitted = ref<boolean>(false);
const max_weight = ref<number>(0);

watch(() => props.classificationResult, (value) => {
  if (value && props.classificationLabels.includes(value)) {
    selectedLabel.value = value;
  } else {
    selectedLabel.value = props.classificationLabels[0];
  }
});

watch([selectedFeature, props.inputData], () => {
  submitted.value = false;
  result.value = null;
  errorMsg.value = "";
})

async function getExplanation() {
  mixpanel.track('Run text explanation', {
    modelId: props.modelId,
    datasetId: props.datasetId
  });
  if (selectedFeature.value && props.inputData[selectedFeature.value].length) {
    try {
      loading.value = true;
      errorMsg.value = "";
      result.value = await api.explainText(
          props.modelId,
          props.datasetId,
          props.inputData,
          selectedFeature.value
      );
      submitted.value = true;
      max_weight.value = Math.max(...Object.values(result.value.explanations).map(elt => Math.max(...elt.map(elt => Math.abs(Object.values(elt)[0])))))
    } catch (error) {
      result.value = null;
      errorMsg.value = error.response.data.detail;
    } finally {
      loading.value = false;
    }
  } else {
    // reset
    errorMsg.value = "";
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
