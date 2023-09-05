<template>
  <div>
    <LoadingFullscreen v-show="loading" name="result" class="pb-6" />
    <v-container v-show="!loading">
      <p v-if="textFeatureNames.length === 0" class="text-center">None</p>
      <div v-else>
        <v-row>
          <v-col cols="5" v-if='textFeatureNames.length > 1'>
            <p class="caption secondary--text text--lighten-2 my-1">Feature</p>
            <v-select dense solo v-model="selectedFeature" :items="textFeatureNames"></v-select>
          </v-col>
          <v-col cols="5">
            <p class="caption secondary--text text--lighten-2 my-1">
              Classification Label
            </p>
            <v-autocomplete dense solo v-model="selectedLabel" :items="classificationLabels"></v-autocomplete>
          </v-col>
          <v-col cols="2" class="d-flex align-center">
            <v-btn tile small color="primary" @click="getExplanation" :disabled="submitted">
              <v-icon left>play_arrow</v-icon>
              Run
            </v-btn>
          </v-col>
        </v-row>
        <div v-if="result != null">
          <p class='caption text-center mb-0'>Word contribution (shap values)</p>
          <p class="result-paragraph">
            <TextExplanationParagraph :weights="result.weights[selectedLabel]" :words="result.words" :max_weight="max_weight" :min_weight="min_weight"></TextExplanationParagraph>
          </p>
        </div>
      </div>
      <p v-if="errorMsg" class="error--text">
        {{ errorMsg }}
      </p>
    </v-container>
  </div>
</template>

<script lang="ts" setup>
import { ref, watch } from 'vue';
import mixpanel from 'mixpanel-browser';
import { ExplainTextResponseDTO } from '@/generated-sources';
import TextExplanationParagraph from './TextExplanationParagraph.vue';
import { api } from '@/api';
import LoadingFullscreen from '@/components/LoadingFullscreen.vue';


interface Props {
  modelId: string,
  datasetId: string,
  textFeatureNames: string[],
  classificationLabels?: string[]
  inputData?: object,
  classificationResult: string
}

const props = withDefaults(defineProps<Props>(), {
  inputData: () => ({}),
  classificationLabels: () => []
});

const loading = ref<boolean>(false);
const selectedFeature = ref<string>(props.textFeatureNames[0]);
const selectedLabel = ref<string>(props.classificationResult || props.classificationLabels[0]);
const errorMsg = ref<string>("");
const result = ref<ExplainTextResponseDTO | null>(null);
const submitted = ref<boolean>(false);
const max_weight = ref<number>(0);
const min_weight = ref<number>(0);

watch(() => props.classificationResult, (value) => {
  if (value && props.classificationLabels.includes(value)) {
    selectedLabel.value = value;
  } else {
    selectedLabel.value = props.classificationLabels[0];
  }
});

watch(() => [props.inputData, selectedFeature.value], () => {
  submitted.value = false;
  result.value = null;
  errorMsg.value = '';
}, { deep: true })


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
      max_weight.value = Math.max(...Object.values(result.value.weights).map(elt => Math.max(...elt)))
      min_weight.value = Math.min(...Object.values(result.value.weights).map(elt => Math.min(...elt)))

    } catch (error) {
      result.value = null;
      errorMsg.value = error.response.data.detail;
    } finally {
      loading.value = false;
    }
  } else {
    // reset
    errorMsg.value = "";
    result.value = null;
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
