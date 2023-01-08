<template>
  <v-card flat>
    <v-card-title>
      Select dataset
    </v-card-title>
    <OverlayLoader :show="loading"/>
    <v-card-text class="scrollable-with-limits">
      <div v-if="datasets.length > 0">
        <v-radio-group v-model="datasetSelected" :disabled="creatingInspection">
          <v-radio
              v-for="n in datasets"
              :key="n.id"
              :label="n.name"
              :value="n"
          ></v-radio>
        </v-radio-group>
      </div>
      <div v-else>No dataset uploaded yet on this project.</div>
      <v-spacer/>
      <div v-if="creatingInspection">
        <span>Scoring the entire dataset of {{ datasetSelected?.size | fileSize }}. This operation can take a while...</span>
        <v-progress-linear
            indeterminate
            color="primary"
            class="mt-2"
        ></v-progress-linear>
      </div>
    </v-card-text>
    <v-card-actions>
      <v-btn text @click="reset()"> Cancel</v-btn>
      <v-spacer></v-spacer>
      <v-btn
          color="primary"
          @click="launchInspector()"
          :disabled="creatingInspection"
      >
        Inspect
      </v-btn>
    </v-card-actions>
  </v-card>

</template>

<script setup lang="ts">
import {DatasetDTO, ModelDTO} from "@/generated-sources";
import {onMounted, ref} from "vue";
import {api} from "@/api";
import mixpanel from "mixpanel-browser";
import {useRouter} from "vue-router/composables";
import OverlayLoader from "@/components/OverlayLoader.vue";

const router = useRouter();

interface Props {
  projectId: number,
  model: ModelDTO
}

const props = defineProps<Props>();
const emit = defineEmits(['cancel'])

const loading = ref<boolean>(false);
const step = ref<number>(1);
const datasets = ref<DatasetDTO[]>([]);
const datasetSelected = ref<DatasetDTO | null>(null);
const datasetFeatures = ref<string[]>([]);
const creatingInspection = ref<boolean>(false);

onMounted(() => {
  loadDatasets();
})

function reset() {
  step.value = 1;
  datasetSelected.value = null;
  datasetFeatures.value = [];
  emit('cancel')
}

async function loadDatasets() {
  loading.value = true;
  datasets.value = await api.getProjectDatasets(props.projectId);
  datasets.value.sort((a, b) =>
      new Date(a.createdDate) < new Date(b.createdDate) ? 1 : -1
  );
  loading.value = false;
}

async function launchInspector() {
  mixpanel.track('Create inspection', {datasetId: datasetSelected.value!.id, modelId: props.model.id});
  try {
    creatingInspection.value = true;
    const inspection = await api.prepareInspection({datasetId: datasetSelected.value!.id, modelId: props.model.id});
    await router.push({name: 'project-inspector', params: {inspectionId: inspection.id.toString()}});
    reset();
  } finally {
    creatingInspection.value = false;
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
