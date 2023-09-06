<template>
  <v-container fluid v-if="model && dataset" class="vc overflow-x-hidden">
    <ValidationObserver ref="dataFormObserver" v-slot="{ changed }">
      <v-row v-if='modelFeatures.length'>
        <v-col cols="12" md="6">
          <v-card outlined>
            <OverlayLoader :show="loadingData" />
            <v-card-title>
              Input Data
              <v-spacer></v-spacer>
              <v-chip v-show="isInputNotOriginal" small label outlined color="accent" class="mx-1 pa-1">
                modified
              </v-chip>
              <v-btn text small @click="resetInput" v-track-click="'Inspection feature reset'" :disabled="!(changed || isInputNotOriginal)">reset
              </v-btn>
              <v-menu left bottom offset-y :close-on-content-click="false">
                <template v-slot:activator="{ on, attrs }">
                  <v-btn icon v-bind="attrs" v-on="on">
                    <v-icon>settings</v-icon>
                  </v-btn>
                </template>
                <v-list dense tile>
                  <v-list-item>
                    <v-btn tile small text color="primary" @click="featuresToView = inputMetaData.map(e => e.name)">All
                    </v-btn>
                    <v-btn tile small text color="secondary" @click="featuresToView = []">None</v-btn>
                  </v-list-item>
                  <v-list-item v-for="f in inputMetaData" :key="f.name">
                    <v-checkbox :label="f.name" :value="f.name" v-model="featuresToView" hide-details class="mt-1"></v-checkbox>
                  </v-list-item>
                </v-list>
              </v-menu>

            </v-card-title>
            <v-card-text v-if="!errorLoadingMetadata && Object.keys(inputMetaData).length > 0" id="inputTextCard">
              <div class="caption error--text">{{ dataErrorMsg }}</div>
              <v-form lazy-validation>
                <div v-for="c in datasetNonTargetColumns" :key="c.name" v-show="featuresToView.includes(c.name)">
                  <ValidationProvider :name="c.name" v-slot="{ changed }">
                    <div class="py-1 d-flex" v-if="isFeatureEditable(c.name)">
                      <label class="info--text">{{ c.name }}</label>
                      <input type="number" v-if="c.type === 'numeric'" v-model="inputData[c.name]" class="common-style-input" :class="{
                        'is-transformed': !changed && transformationModifications.hasOwnProperty(c.name) && inputData[c.name] === transformationModifications[c.name],
                        'is-changed': changed || Number(inputData[c.name]) !== originalData[c.name]
                      }" @change="onValuePerturbation(c)" required />
                      <textarea v-if="c.type === 'text'" v-model="inputData[c.name]" :rows="!inputData[c.name] ? 1 : Math.min(15, parseInt(inputData[c.name].length / 40) + 1)" class="common-style-input" :class="{
                        'is-transformed': !changed && transformationModifications.hasOwnProperty(c.name) && inputData[c.name] === transformationModifications[c.name],
                        'is-changed': changed || inputData[c.name] !== originalData[c.name]
                      }" @change="onValuePerturbation(c)" required></textarea>
                      <select v-if="c.type === 'category'" v-model="inputData[c.name]" class="common-style-input" :class="{
                        'is-transformed': !changed && transformationModifications.hasOwnProperty(c.name) && inputData[c.name] === transformationModifications[c.name],
                        'is-changed': changed || inputData[c.name] !== originalData[c.name]
                      }" @change="onValuePerturbation(c)" required>
                        <option v-for="k in c.values" :key="k" :value="k">{{ k }}</option>
                      </select>
                      <div class="d-flex flex-column">
                        <FeedbackPopover v-if="!isMiniMode" :inputLabel="c.name" :inputValue="inputData[c.name]" :originalValue="originalData[c.name]" :inputType="c.type" @submit="emit(changed ? 'submitValueVariationFeedback' : 'submitValueFeedback', $event)" />
                        <TransformationPopover v-if="catalogStore.transformationFunctionsByColumnType.hasOwnProperty(c.type)" :column="c.name" :column-type="c.type" />
                        <PushPopover
                            type="contribution"
                            :column="c.name"
                            key="a"
                        />
                        <PushPopover
                            type="perturbation"
                            :column="c.name"
                            key="b"
                        />
                      </div>
                    </div>
                    <div class="py-1 d-flex" v-else>
                      <label class="info--text">{{ c.name }}</label>
                      <span>{{ inputData[c.name] }}</span>
                    </div>
                  </ValidationProvider>
                </div>
              </v-form>
            </v-card-text>

            <v-card-text v-else>
              Could not load metadata. Please try another dataset.
              <p class="error--text">{{ errorLoadingMetadata }}</p>
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="12" md="6">
          <PredictionResults v-if='InspectorUtils.hasFeature(InspectorFeature.PREDICTION_RESULT, model)' :model='model'
                             :dataset-id='dataset.id' :targetFeature='dataset.target' :modelFeatures='modelFeatures'
                             :classificationLabels='model.classificationLabels' :predictionTask='model.modelType'
                             :inputData='inputData' :modified='changed || isInputNotOriginal'
                             :debouncingTimeout='debouncingTimeout' @result='setResult' />
          <GenerationResults v-if='InspectorUtils.hasFeature(InspectorFeature.GENERATION_RESULT, model)' :model='model'
                             :dataset-id='dataset.id' :targetFeature='dataset.target' :modelFeatures='modelFeatures'
                             :classificationLabels='model.classificationLabels' :predictionTask='model.modelType'
                             :inputData='inputData' :modified='changed || isInputNotOriginal'
                             :debouncingTimeout='debouncingTimeout' @result='setResult' />
          <InspectorExplanation v-if='InspectorUtils.hasFeature(InspectorFeature.EXPLANATION, model)'
                                :dataset='dataset' :model='model' :input-data='inputData'
                                :classification-result='classificationResult' :model-features='modelFeatures'
                                :input-meta-data='inputMetaData' />
        </v-col>
      </v-row>
    </ValidationObserver>
  </v-container>
</template>

<script setup lang="ts">
import OverlayLoader from '@/components/OverlayLoader.vue';
import PredictionResults from './PredictionResults.vue';
import FeedbackPopover from '@/components/FeedbackPopover.vue';
import { DatasetDTO, ModelType } from '@/generated-sources';
import mixpanel from 'mixpanel-browser';
import { anonymize } from '@/utils';
import _ from 'lodash';
import TransformationPopover from '@/components/TransformationPopover.vue';
import { useCatalogStore } from '@/stores/catalog';
import { computed, onMounted, ref, watch } from 'vue';
import PushPopover from '@/components/PushPopover.vue';
import InspectorExplanation from '@/views/main/project/InspectorExplanation.vue';
import { InspectorFeature, InspectorUtils } from '@/utils/inspector-utils';
import { ModelDTO } from '@/generated/client';
import GenerationResults from '@/views/main/project/GenerationResults.vue';

const catalogStore = useCatalogStore();

interface Props {
  model: ModelDTO;
  dataset: DatasetDTO;
  originalData: any; // used for the variation feedback
  transformationModifications: any; // used for the variation feedback
  inputData: { [key: string]: string };
  isMiniMode?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  isMiniMode: false
});

const debouncingTimeout: number = 500;

const loadingData = ref(false);
const featuresToView = ref<string[]>([])
const errorLoadingMetadata = ref("")
const dataErrorMsg = ref("")
const classificationResult = ref("")
const dataFormObserver = ref(null);

const inputMetaData = computed(() => {
  if (!props.model) {
    return [];
  }

  return Object.entries(props.dataset.columnTypes)
    .map(([name, type]) => ({
      name,
      type,
      values: props.dataset.categoryFeatures[name] ?? []
      // Provide an empty list in case of null due to DB migration
    }))
})

const parseIfNumber = (value: any, giskardType: string) => {
  if (giskardType === 'numeric') {
    return Number(value);
  }
  return value;
}

const inputDataFormatted = computed(() => {
  let result = {};
  for (const [name, value] of Object.entries(props.inputData)) {
    result[name] = parseIfNumber(value, props.dataset.columnTypes[name]);
  }
  return result;
})

const originalDataFormatted = computed(() => {
  let result = {};
  for (const [name, value] of Object.entries(props.originalData)) {
    result[name] = parseIfNumber(value, props.dataset.columnDtypes[name]);
  }
  return result;
})

const isInputNotOriginal = computed(() => {
  const result = JSON.stringify(originalDataFormatted.value) !== JSON.stringify({ ...inputDataFormatted.value, ...props.transformationModifications })

  if (!result) {
    dataFormObserver.value && (dataFormObserver.value as HTMLFormElement).reset();
  }

  return result;
})

const modelFeatures = computed(() => {
  return inputMetaData.value
    .filter(x => (x.name !== props.dataset.target) && (!props.model.featureNames || props.model.featureNames.includes(x.name)))
    .map(x => x.name);
})

const datasetNonTargetColumns = computed(() => {
  return _.sortBy(inputMetaData.value.filter(x => x.name !== props.dataset.target),
    e => !props.model.featureNames?.includes(e.name),
    'name'
  )
})

function setResult(r: string) {
  if (props.model.modelType === ModelType.CLASSIFICATION) {
    classificationResult.value = r
  }
}

function resetInput() {
  emit('reset');
  dataFormObserver.value && (dataFormObserver.value as HTMLFormElement).reset();
}

function isFeatureEditable(featureName: string) {
  if (!props.model.featureNames || props.model.featureNames.length == 0) {
    // if user doesn't specify feature names consider all columns as feature names
    return true;
  }
  return props.model.featureNames.includes(featureName)
}

async function onValuePerturbation(featureMeta) {
  mixpanel.track("Feature perturbation", {
    columnType: featureMeta.type,
    featureName: anonymize(featureMeta.name),
    modelId: props.model.id,
    datasetId: props.dataset.id
  })
  emit('update:inputData', props.inputData)
}

async function loadMetaData() {
  featuresToView.value = inputMetaData.value.map(e => e.name)
}

const emit = defineEmits(['reset', 'update:inputData', 'submitValueVariationFeedback', 'submitValueFeedback']);

watch(() => props.originalData, () => {
  resetInput();
})

watch(() => inputMetaData.value, async () => {
  await loadMetaData();
})

onMounted(async () => {
  await loadMetaData();
});
</script>

<style scoped lang="scss">
label {
  display: inline-block;
  width: 40%;
}

.common-style-input {
  flex-grow: 1;
  border: 1px solid #e4e4e4;
  border-radius: 5px;
  line-height: 24px;
  min-height: 24px;
  width: 56%;
  padding-left: 6px;
  padding-right: 6px;
}

select.common-style-input {
  /* -moz-appearance: menulist-button;
  -webkit-appearance: menulist-button; */
  /* OR */
  -moz-appearance: none;
  -webkit-appearance: none;
  appearance: none;
  background-image: url('data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22292.4%22%20height%3D%22292.4%22%3E%3Cpath%20fill%3D%22%23007CB2%22%20d%3D%22M287%2069.4a17.6%2017.6%200%200%200-13-5.4H18.4c-5%200-9.3%201.8-12.9%205.4A17.6%2017.6%200%200%200%200%2082.2c0%205%201.8%209.3%205.4%2012.9l128%20127.9c3.6%203.6%207.8%205.4%2012.8%205.4s9.2-1.8%2012.8-5.4L287%2095c3.5-3.5%205.4-7.8%205.4-12.8%200-5-1.9-9.2-5.5-12.8z%22%2F%3E%3C%2Fsvg%3E');
  background-repeat: no-repeat, repeat;
  background-position: right .3em top 50%, 0 0;
  background-size: .65em auto, 100%;
}

.common-style-input.is-changed {
  background-color: #AD14572B;
  /* accent color but with opacity */
}

.common-style-input.is-transformed {
  background-color: #d1ecf1;
}

.v-card__subtitle,
.v-card__text,
.v-card__title {
  padding-bottom: 8px;
}

>>>.v-tabs.no-tab-header>.v-tabs-bar {
  display: none;
}
</style>
