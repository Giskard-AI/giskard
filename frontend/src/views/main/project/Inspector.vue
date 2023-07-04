<template>
  <v-container fluid v-if="model && dataset" class="vc overflow-x-hidden">
    <ValidationObserver ref="dataFormObserver" v-slot="{ dirty }">
      <v-row v-if='modelFeatures.length'>
        <v-col cols="12" md="6">
          <v-card outlined>
            <OverlayLoader :show="loadingData" />
            <v-card-title>
              Input Data
              <v-spacer></v-spacer>
              <v-chip v-show="dirty || isInputNotOriginal" small label outlined color="accent" class="mx-1 pa-1">
                modified
              </v-chip>
              <v-btn text small @click="resetInput" v-track-click="'Inspection feature reset'" :disabled="!(dirty || isInputNotOriginal)">reset
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
                  <ValidationProvider :name="c.name" v-slot="{ dirty }">
                    <div class="py-1 d-flex" v-if="isFeatureEditable(c.name)">
                      <label class="info--text">{{ c.name }}</label>
                      <input type="number" v-if="c.type === 'numeric'" v-model="inputData[c.name]" class="common-style-input" :class="{
                        'is-transformed': !dirty && transformationModifications.hasOwnProperty(c.name) && inputData[c.name] === transformationModifications[c.name],
                        'is-dirty': dirty || inputData[c.name] !== originalData[c.name]
                      }" @change="onValuePerturbation(c)" required />
                      <textarea v-if="c.type === 'text'" v-model="inputData[c.name]" :rows="!inputData[c.name] ? 1 : Math.min(15, parseInt(inputData[c.name].length / 40) + 1)" class="common-style-input" :class="{
                        'is-transformed': !dirty && transformationModifications.hasOwnProperty(c.name) && inputData[c.name] === transformationModifications[c.name],
                        'is-dirty': dirty || inputData[c.name] !== originalData[c.name]
                      }" @change="onValuePerturbation(c)" required></textarea>
                      <select v-if="c.type === 'category'" v-model="inputData[c.name]" class="common-style-input" :class="{
                        'is-transformed': !dirty && transformationModifications.hasOwnProperty(c.name) && inputData[c.name] === transformationModifications[c.name],
                        'is-dirty': dirty || inputData[c.name] !== originalData[c.name]
                      }" @change="onValuePerturbation(c)" required>
                        <option v-for="k in c.values" :key="k" :value="k">{{ k }}</option>
                      </select>
                      <div class="d-flex flex-column">
                        <FeedbackPopover v-if="!isMiniMode" :inputLabel="c.name" :inputValue="inputData[c.name]" :originalValue="originalData[c.name]" :inputType="c.type" @submit="emit(dirty ? 'submitValueVariationFeedback' : 'submitValueFeedback', $event)" />
                        <TransformationPopover v-if="catalogStore.transformationFunctionsByColumnType.hasOwnProperty(c.type)" :column="c.name" :column-type="c.type" />
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
          <PredictionResults :model="model" :dataset-id="dataset.id" :targetFeature="dataset.target" :modelFeatures="modelFeatures" :classificationLabels="model.classificationLabels" :predictionTask="model.modelType" :inputData="inputData" :modified="dirty || isInputNotOriginal" :debouncingTimeout="debouncingTimeout" @result="setResult" />
          <v-card class="mb-4" outlined>
            <v-card-title>
              Explanation
            </v-card-title>
            <v-card-text>
              <v-tabs :class="{ 'no-tab-header': !isClassification(model.modelType) || textFeatureNames.length === 0 }">
                <v-tab v-if='modelFeatures.length > 1'>
                  <v-icon left>mdi-align-horizontal-left</v-icon>
                  Global
                </v-tab>

                <v-tooltip bottom :disabled="textFeatureNames.length !== 0">
                  <template v-slot:activator="{ on, attrs }">
                    <div class="d-flex" v-on="on" v-bind="attrs">
                      <v-tab :disabled="!textFeatureNames.length">
                        <v-icon left>text_snippet</v-icon>
                        Text
                      </v-tab>
                    </div>
                  </template>
                  <span>Text explanation is not available because your model does not contain any text features</span>
                </v-tooltip>


                <v-tab-item v-if='modelFeatures.length > 1'>

                  <PredictionExplanations :modelId="model.id" :datasetId="dataset.id" :targetFeature="dataset.target" :classificationLabels="model.classificationLabels" :predictionTask="model.modelType" :inputData="inputData" :modelFeatures="modelFeatures" :debouncingTimeout="debouncingTimeout" />
                </v-tab-item>
                <v-tab-item v-if='textFeatureNames.length'>
                  <TextExplanation :modelId="model.id" :datasetId="dataset.id" :textFeatureNames="textFeatureNames" :classificationLabels="model.classificationLabels" :classificationResult="classificationResult" :inputData="inputData" />
                </v-tab-item>
              </v-tabs>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </ValidationObserver>
  </v-container>
</template>

<script setup lang="ts">
import OverlayLoader from '@/components/OverlayLoader.vue';
import PredictionResults from './PredictionResults.vue';
import PredictionExplanations from './PredictionExplanations.vue';
import TextExplanation from './TextExplanation.vue';
import FeedbackPopover from '@/components/FeedbackPopover.vue';
import { DatasetDTO, ModelDTO } from "@/generated-sources";
import { isClassification } from "@/ml-utils";
import mixpanel from "mixpanel-browser";
import { anonymize } from "@/utils";
import _ from 'lodash';
import TransformationPopover from "@/components/TransformationPopover.vue";
import { useCatalogStore } from "@/stores/catalog";
import { onMounted, ref, computed, watch } from 'vue';

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
})

const loadingData = ref(false);
const featuresToView = ref<string[]>([])
const errorLoadingMetadata = ref("")
const dataErrorMsg = ref("")
const classificationResult = ref("")
const debouncingTimeout = ref(500);
const dataFormObserver = ref(null);

const inputMetaData = computed(() => {
  if (!props.model) {
    return [];
  }

  return Object.entries(props.dataset.columnTypes)
      .map(([name, type]) => ({
          name,
          type,
          values: props.dataset.categoryFeatures ?
              props.dataset.categoryFeatures[name] : []
              // Provide an empty list in case of null due to DB migration
      }))
})

const isInputNotOriginal = computed(() => {
  return JSON.stringify(props.inputData) !== JSON.stringify({ ...props.originalData, ...props.transformationModifications })
})

const textFeatureNames = computed(() => {
  return inputMetaData.value.filter(e => e.type == 'text').map(e => e.name)
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
  if (isClassification(props.model.modelType)) {
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

.common-style-input.is-dirty {
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
