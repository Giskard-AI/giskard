<template>
  <v-container v-if="inspection" fluid class="vc">
    <v-row align="center" no-gutters>
      <v-col lg="6" sm="12">
        <v-toolbar class='data-explorer-toolbar' flat>
          <v-tooltip bottom min-width="400">
            <template v-slot:activator="{ on, attrs }">
              <v-icon v-on="on" class="pr-16" medium>info</v-icon>
            </template>
            <h3> Debugging session </h3>
            <div class="d-flex">
              <div> Id</div>
              <v-spacer/>
              <div> {{ inspection.id }}</div>
            </div>
            <div class="d-flex">
              <div> Name</div>
              <v-spacer/>
              <div class="pl-5"> {{ inspection.name || "-" }}</div>
            </div>
            <br/>
            <h3> Model </h3>
            <div class="d-flex">
              <div> Id</div>
              <v-spacer/>
              <div> {{ inspection.model.id }}</div>
            </div>
            <div class="d-flex">
              <div> Name</div>
              <v-spacer/>
              <div class="pl-5"> {{ inspection.model.name }}</div>
            </div>
            <br/>
            <h3> Dataset </h3>
            <div class="d-flex">
              <div> Id</div>
              <v-spacer/>
              <div> {{ inspection.dataset.id }}</div>
            </div>
            <div class="d-flex pb-3">
              <div> Name</div>
              <v-spacer/>
              <div class="pl-5"> {{ $tags(inspection.dataset.name) }}</div>
            </div>
          </v-tooltip>
          <span class='subtitle-1 mr-2'>Dataset Explorer</span>
          <v-btn icon @click='shuffleMode = !shuffleMode'>
            <v-icon v-if='shuffleMode' color='primary'>mdi-shuffle-variant</v-icon>
            <v-icon v-else>mdi-shuffle-variant</v-icon>
          </v-btn>
          <v-btn :disabled='!canPrevious' icon @click='previous'>
            <v-icon>mdi-skip-previous</v-icon>
          </v-btn>
          <v-btn :disabled='!canNext' icon @click='next'>
            <v-icon>mdi-skip-next</v-icon>
          </v-btn>

          <span class='caption grey--text' v-if="totalRows > 0">
            Entry #{{ totalRows === 0 ? 0 : rowNb + 1 }} / {{ totalRows }}
          </span>
          <span v-show="originalData && isDefined(originalData['Index'])" class='caption grey--text'
                style='margin-left: 15px'>Row Index {{ originalData['Index'] + 1 }}</span>
          <v-chip class="ml-2" outlined link :color="inspection.sample ? 'purple' : 'primary'"
                  @click="handleSwitchSample" x-small>
            {{ inspection.sample ? 'Sample' : 'Whole' }} data
          </v-chip>
        </v-toolbar>
      </v-col>
      <v-col lg="6" sm="12" class="pl-4">
        <v-row no-gutters align="center">
          <v-col cols="8" class="pb-4">
            <SlicingFunctionSelector label="Slice to apply" :project-id="projectId" :full-width="false" :icon="true"
                                     class="mr-3" :allow-no-code-slicing="true" @onChanged="processDataset"
                                     :value.sync="selectedSlicingFunction.uuid"
                                     :args.sync="selectedSlicingFunction.params" :dataset="inspection.dataset"/>
          </v-col>
          <v-col cols="4" class="d-flex pl-2">
            <InspectionFilter :is-target-available="isDefined(inspection.dataset.target)" :labels="labels"
                              :model-type="inspection.model.modelType" @input="f => filter = f"
                              :inspectionId="inspectionId" :value="filter"/>
          </v-col>
        </v-row>
      </v-col>
    </v-row>
    <Inspector :dataset='inspection.dataset' :inputData.sync='inputData' :model='inspection.model'
               :originalData='originalData' :transformationModifications="modifications" class='px-0'
               @reset='resetInput' @submitValueFeedback='submitValueFeedback'
               @submitValueVariationFeedback='submitValueVariationFeedback' v-if="totalRows > 0"
               :key="inputData._GISKARD_INDEX_" :project-id="projectId"/>
    <v-alert v-else border="bottom" colored-border type="warning" class="mt-8" elevation="2">
      No data matches the selected filter.<br/>
      In order to show data, please refine the filter's criteria.
    </v-alert>


    <!-- For general feedback -->
    <v-tooltip left>
      <template v-slot:activator='{ on, attrs }'>
        <v-btn :class="feedbackPopupToggle ? 'secondary' : 'primary'" bottom fab fixed class="zindex-10" right
               v-bind='attrs' @click='feedbackPopupToggle = !feedbackPopupToggle' v-on='on'>
          <v-icon v-if='feedbackPopupToggle'>mdi-close</v-icon>
          <v-icon v-else>mdi-message-plus</v-icon>
        </v-btn>
      </template>
      <span v-if='feedbackPopupToggle'>Close</span>
      <span v-else>Feedback</span>
    </v-tooltip>
    <v-overlay :value='feedbackPopupToggle' :z-index='10'></v-overlay>
    <v-card v-if='feedbackPopupToggle' id='feedback-card' color='primary' dark>
      <v-card-title>Is this input case insightful?</v-card-title>
      <v-card-text class='px-3 py-0'>
        <v-radio-group v-model='feedbackChoice' class='mb-2 mt-0' dark hide-details row>
          <v-radio label='Yes' value='yes'></v-radio>
          <v-radio label='No' value='no'></v-radio>
          <v-radio label='Other' value='other'></v-radio>
        </v-radio-group>
        <v-textarea v-model='feedback' :disabled='feedbackSubmitted' hide-details no-resize outlined placeholder='Why?'
                    rows='2'></v-textarea>
      </v-card-text>
      <p v-if='feedbackError' class='caption error--text mb-0'>{{ feedbackError }}</p>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn :disabled='feedbackSubmitted' light small text @click='clearFeedback'>Cancel</v-btn>
        <v-btn :disabled='!(feedback && feedbackChoice) || feedbackSubmitted' class='mx-1' color='white' light small
               @click='submitGeneralFeedback'>
          Send
        </v-btn>
        <v-icon v-show='feedbackSubmitted' color='white'>mdi-check</v-icon>
      </v-card-actions>
    </v-card>
    <!-- End For general feedback -->
  </v-container>
</template>

<script setup lang='ts'>
import {computed, onMounted, onUnmounted, ref, watch} from 'vue';
import {api} from '@/api';
import Inspector from './Inspector.vue';
import Mousetrap from 'mousetrap';
import {
  CreateFeedbackDTO,
  DatasetProcessingResultDTO,
  Filter,
  InspectionDTO,
  ModelType,
  ParameterizedCallableDTO,
  RowFilterType
} from '@/generated-sources';
import mixpanel from "mixpanel-browser";
import _ from "lodash";
import InspectionFilter from './InspectionFilter.vue';
import SlicingFunctionSelector from "@/views/main/utils/SlicingFunctionSelector.vue";
import {useCatalogStore} from "@/stores/catalog";
import {storeToRefs} from "pinia";
import {useInspectionStore} from "@/stores/inspection";
import {$vfm} from "vue-final-modal";
import BlockingLoadingModal from "@/views/main/project/modals/BlockingLoadingModal.vue";
import {confirm} from "@/utils/confirmation.utils";
import {usePushStore} from "@/stores/push";
import {useDebuggingSessionsStore} from "@/stores/debugging-sessions";
import {$tags} from "@/utils/nametags.utils";

interface CreatedFeedbackCommonDTO {
  targetFeature?: string | null;
  userData: string;
  modelId: string;
  datasetId: string;
  originalData: string;
  projectId: number
}

interface Props {
  inspectionId: number;
  projectId: number;
}

const props = defineProps<Props>();

const inspection = ref<InspectionDTO | null>(null);
const mouseTrap = new Mousetrap();
const loadingData = ref(false);
const loadingProcessedDataset = ref(false); // specific boolean for slice loading because it can take a while...
const inputData = ref({});
const originalData = ref<any>({});
const rowNb = ref(0);
const shuffleMode = ref(false);
const dataErrorMsg = ref('');

const feedbackPopupToggle = ref(false);
const feedback = ref('');
const feedbackChoice = ref(null);
const feedbackError = ref('');
const feedbackSubmitted = ref(false);
const labels = ref<string[]>([]);
const filter = ref<Filter>({
  inspectionId: props.inspectionId,
  type: RowFilterType.ALL
});

const {selectedSlicingFunction} = storeToRefs(useDebuggingSessionsStore())

const dataProcessingResult = ref<DatasetProcessingResultDTO | null>(null);

const totalRows = ref(0);
const mt = ModelType;
const rows = ref<Record<string, any>[]>([]);
const numberOfRows = ref(0);
const itemsPerPage = 200;
const rowIdxInPage = ref(0);
const regressionThreshold = ref(0.1);
const percentRegressionUnit = ref(true);

const canPrevious = computed(() => rowNb.value > 0);
const canNext = computed(() => rowNb.value < totalRows.value - 1);
const {transformationFunctions} = storeToRefs(useInspectionStore());

function commonFeedbackData(): CreatedFeedbackCommonDTO {
  return {
    targetFeature: inspection.value?.dataset.target,
    userData: JSON.stringify(inputData.value),
    modelId: inspection.value!.model.id,
    datasetId: inspection.value!.dataset.id,
    originalData: JSON.stringify(originalData.value),
    projectId: props.projectId
  };
}

function clearFeedback() {
  feedback.value = '';
  feedbackError.value = '';
  feedbackSubmitted.value = false;
  feedbackChoice.value = null;
  feedbackPopupToggle.value = false;
}

function isDefined(val: any): boolean {
  return !_.isNil(val);
}

function previous() {
  if (canPrevious.value) {
    clearFeedback();
    rowNb.value -= 1;
    debouncedUpdateRow();
  }
}

function next() {
  if (canNext.value) {
    clearFeedback();
    rowNb.value += 1;
    debouncedUpdateRow();
  }
}

watch(() => inputData.value, async (newValue, oldValue) => {
  console.log("RowNb changed");
  const pushStore = usePushStore();
  await pushStore.fetchPushSuggestions(inspection.value!.model.id, inspection.value!.dataset.id, rowNb.value, newValue, modelFeatures.value);
});

async function submitGeneralFeedback() {
  const newFeedback: CreateFeedbackDTO = {
    ...commonFeedbackData(),
    feedbackType: 'general',
    feedbackChoice: feedbackChoice.value,
    feedbackMessage: feedback.value
  };

  try {
    feedbackSubmitted.value = true;
    await doSubmitFeedback(newFeedback);
    feedbackPopupToggle.value = false;
  } catch (err) {
    feedbackError.value = err.response.data.detail;
  }
}

async function submitValueFeedback(userData: object) {
  const newFeedback: CreateFeedbackDTO = {
    ...commonFeedbackData(),
    feedbackType: 'value',
    ...userData
  };
  await doSubmitFeedback(newFeedback);
}

async function submitValueVariationFeedback(userData: object) {
  const newFeedback: CreateFeedbackDTO = {
    ...commonFeedbackData(),
    feedbackType: 'value perturbation',
    ...userData
  };
  await doSubmitFeedback(newFeedback);
}

const debouncedUpdateRow = _.debounce(async () => {
  await updateRow(false);
}, 150);

async function applyFilter(nv, ov) {
  if (JSON.stringify(nv) === JSON.stringify(ov)) {
    return;
  }
  await updateRow(true);
}

watch(() => [
  inspection.value?.id,
  regressionThreshold.value,
  filter.value,
  shuffleMode.value,
  percentRegressionUnit.value,
  dataProcessingResult.value
], async (nv, ov) => applyFilter(nv, ov), {deep: true, immediate: false});

async function updateRow(forceFetch) {
  await fetchRows(rowNb.value, forceFetch);
  assignCurrentRow(forceFetch)
}

/**
 * Calling fetch rows if necessary, i.e. when start or end of the page
 * @param rowIdxInResults index of the row in the results
 * @param forceFetch
 */
async function fetchRows(rowIdxInResults: number, forceFetch: boolean) {
  const remainder = rowIdxInResults % itemsPerPage;
  const newPage = Math.floor(rowIdxInResults / itemsPerPage);
  if ((rowIdxInResults > 0 && remainder === 0) || forceFetch) {
    const result = await api.getDatasetRows(inspection.value!.dataset.id,
        newPage * itemsPerPage, itemsPerPage, {
          filter: {
            ...filter.value,
            inspectionId: props.inspectionId
          },
          removeRows: dataProcessingResult.value?.filteredRows
        }, inspection.value!.sample, shuffleMode.value)
    rows.value = result.content;
    numberOfRows.value = result.totalItems;
  }
}


function assignCurrentRow(forceFetch: boolean) {
  rowIdxInPage.value = rowNb.value % itemsPerPage;
  loadingData.value = true;

  inputData.value = rows.value[rowIdxInPage.value];
  originalData.value = {...inputData.value}; // deep copy to avoid caching mechanisms
  dataErrorMsg.value = '';
  loadingData.value = false;
  totalRows.value = numberOfRows.value;
  if (forceFetch) {
    rowNb.value = 0;
  }
}


const modifications = computed(() => dataProcessingResult.value?.modifications?.find(m => m.rowId === originalData.value['_GISKARD_INDEX_'])?.modifications ?? {});

function resetInput() {
  inputData.value = {
    ...originalData.value,
    ...modifications.value
  };
}

async function doSubmitFeedback(payload: CreateFeedbackDTO) {
  mixpanel.track('Submit feedback', {
    datasetId: payload.datasetId,
    feedbackChoice: payload.feedbackChoice,
    feedbackType: payload.feedbackType,
    modelId: payload.modelId,
    projectId: payload.projectId
  });
  await api.submitFeedback(payload, payload.projectId);
}

const transformationPipeline = computed(() => Object.values(transformationFunctions.value))

watch(() => transformationPipeline.value, processDataset, {deep: true})

watch(() => props.inspectionId, async (nv, ov) => {
  if (nv !== ov) {
    await init();
  }
});

watch(() => selectedSlicingFunction.value, async () => {
  console.log("watch updated");
  await processDataset();
})

async function processDataset() {
  const pipeline = [selectedSlicingFunction.value, ...transformationPipeline.value]
      .filter(callable => !!callable.uuid) as Array<ParameterizedCallableDTO>;

  loadingProcessedDataset.value = true;
  dataProcessingResult.value = await api.datasetProcessing(props.projectId, inspection.value!.dataset.id, pipeline, inspection.value!.sample)
  loadingProcessedDataset.value = false;
}

function bindKeys() {
  mouseTrap.bind('left', previous);
  mouseTrap.bind('right', next);
}

function resetKeys() {
  mouseTrap.reset();
}


async function init() {
  inspection.value = await api.getInspection(props.inspectionId);
  useInspectionStore().$reset();
  await useCatalogStore().loadCatalog(props.projectId);
}

onMounted(async () => {
  labels.value = await api.getLabelsForTarget(props.inspectionId);
  bindKeys();
  await init();
});

onUnmounted(() => {
  resetKeys();
});

async function handleSwitchSample() {
  if (inspection.value!.sample) {
    const confirmed = await confirm($vfm, 'Inspect whole dataset', 'Opening the debugger on the whole data might cause performance issues');
    if (!confirmed) {
      return;
    }
  }

  await $vfm.show({
    component: BlockingLoadingModal,
    bind: {
      title: "Preprocessing dataset",
      text: "Please wait. This operation might take some time."
    },
    on: {
      async mounted(close) {
        try {
          inspection.value = await api.updateInspectionName(inspection.value!.id, {
            name: inspection.value!.name,
            datasetId: inspection.value!.dataset.id,
            modelId: inspection.value!.model.id,
            sample: !inspection.value!.sample
          });
          await updateRow(true);
        } finally {
          close();
        }
      }
    }
  });
}

const modelFeatures = computed(() => {
  return inputMetaData
      .value
      //.filter(x => (!inspection.value?.model.featureNames || inspection.value.model.featureNames.includes(x.name)))
      .map(x => x.name);
});

const inputMetaData = computed(() => {
  if (!inspection.value?.model) {
    return [];
  }

  return Object.entries(inspection.value?.dataset.columnTypes)
      .map(([name, type]) => ({
        name,
        type,
        values: inspection.value?.dataset.categoryFeatures[name]
      }))
});
</script>

<style scoped>
.data-explorer-toolbar .v-btn {
  height: 36px;
  width: 36px;
}

#feedback-card {
  z-index: 10;
  width: 42vw;
  position: fixed;
  opacity: 0.96;
  right: 8px;
  bottom: 80px;
}

.zindex-10 {
  z-index: 10;
}

#feedback-card .v-card__title {
  font-size: 1.1rem;
  padding: 8px 12px 0;
}
</style>
