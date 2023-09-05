<template>
  <v-card class='mb-4' outlined>
    <v-card-title>
      Explanation
    </v-card-title>
    <v-card-text>
      <v-tabs :class="{ 'no-tab-header': !isClassification(model.modelType) || textFeatureNames.length === 0 }">
        <v-tab v-if='modelFeatures.length > 1'>
          <v-icon left>mdi-align-horizontal-left</v-icon>
          Global
        </v-tab>

        <v-tooltip bottom :disabled='textFeatureNames.length !== 0'>
          <template v-slot:activator='{ on, attrs }'>
            <div class='d-flex' v-on='on' v-bind='attrs'>
              <v-tab :disabled='!textFeatureNames.length'>
                <v-icon left>text_snippet</v-icon>
                Text
              </v-tab>
            </div>
          </template>
          <span>Text explanation is not available because your model does not contain any text features</span>
        </v-tooltip>


        <v-tab-item v-if='modelFeatures.length > 1'>

          <PredictionExplanations :modelId='model.id' :datasetId='dataset.id' :targetFeature='dataset.target'
                                  :classificationLabels='model.classificationLabels' :predictionTask='model.modelType'
                                  :inputData='inputData' :modelFeatures='modelFeatures'
                                  :debouncingTimeout='DEBOUNCING_TIMEOUT' />
        </v-tab-item>
        <v-tab-item v-if='textFeatureNames.length'>
          <TextExplanation v-if='model.modelType == ModelType.CLASSIFICATION' :modelId='model.id'
                           :datasetId='dataset.id' :textFeatureNames='textFeatureNames'
                           :classificationLabels='model.classificationLabels'
                           :classificationResult='classificationResult' :inputData='inputData' />
          <RegressionTextExplanation v-else :modelId='model.id' :datasetId='dataset.id'
                                     :textFeatureNames='textFeatureNames' :inputData='inputData' />
        </v-tab-item>
      </v-tabs>
    </v-card-text>
  </v-card>
</template>

<script setup lang='ts'>
import { isClassification } from '@/ml-utils';
import { ColumnType, DatasetDTO, ModelType } from '@/generated-sources';
import PredictionExplanations from '@/views/main/project/PredictionExplanations.vue';
import TextExplanation from '@/views/main/project/TextExplanation.vue';
import RegressionTextExplanation from '@/views/main/project/RegressionTextExplanation.vue';
import { computed } from 'vue';
import { ModelDTO } from '@/generated/client';

interface Props {
  model: ModelDTO;
  dataset: DatasetDTO;
  inputData: { [key: string]: string };
  classificationResult: string;
  modelFeatures: string[];
  inputMetaData: { name: string, type: ColumnType, values: string[] }[];
}

const props = defineProps<Props>();

const DEBOUNCING_TIMEOUT = 500;


const textFeatureNames = computed(() => {
  return props.inputMetaData.filter(e => e.type == 'text').map(e => e.name);
});
</script>

