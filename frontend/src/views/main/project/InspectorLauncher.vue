<template>
  <v-card flat>
    <v-card-title>
      Select dataset
    </v-card-title>
    <OverlayLoader :show="loading" />
    <v-card-text class="scrollable-with-limits">
      <div v-if="datasets.length > 0">
        <v-radio-group v-model="datasetSelected" :disabled="creatingInspection">
          <v-radio v-for="n in datasets" :key="n.id" :label="n.name || n.id" :value="n"></v-radio>
        </v-radio-group>
      </div>
      <div v-else>No dataset uploaded yet on this project.</div>
      <v-spacer />
      <div v-if="creatingInspection">
        <span>Scoring the entire dataset of {{ datasetSelected?.originalSizeBytes | fileSize }}. This operation can take a while...</span>
        <v-progress-linear indeterminate color="primary" class="mt-2"></v-progress-linear>
      </div>
    </v-card-text>
    <v-card-actions>
      <v-btn text @click="reset()"> Cancel</v-btn>
      <v-spacer></v-spacer>
      <v-btn color="primaryLight" class="primaryLightBtn" @click="launchInspector()" :disabled="creatingInspection">
        Debug
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
import { DatasetDTO, ModelDTO } from "@/generated-sources";
import { onMounted, ref } from "vue";
import { api } from "@/api";
import { TYPE } from "vue-toastification";
import mixpanel from "mixpanel-browser";
import { useRouter } from "vue-router/composables";
import OverlayLoader from "@/components/OverlayLoader.vue";
import { useMainStore } from "@/stores/main";
import { useDebuggingSessionsStore } from "@/stores/debugging-sessions";
import { useMLWorkerStore } from '@/stores/ml-worker';

const router = useRouter();

const debuggingSessionsStore = useDebuggingSessionsStore();
const mlWorkerStore = useMLWorkerStore();

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


onMounted(async () => {
  await loadDatasets();
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
  mixpanel.track('Create debugging session', {
    source: "InspectorLauncher",
    datasetId: datasetSelected.value!.id,
    modelId: props.model.id
  });
  try {
    creatingInspection.value = true;

    await mlWorkerStore.checkExternalWorkerConnection();

    if (!mlWorkerStore.isExternalWorkerConnected) {
      useMainStore().addNotification({
        content: 'ML Worker is not connected. Please start the ML Worker first and try again.',
        color: TYPE.ERROR,
      });
      throw new Error('ML Worker is not connected. Please start the ML Worker first and try again.');
    }

    const inspection = await api.prepareInspection({
      datasetId: datasetSelected.value!.id,
      modelId: props.model.id,
      name: "",
      sample: true
    });

    debuggingSessionsStore.setCurrentDebuggingSessionId(inspection.id);

    await router.push({
      name: 'inspection', params: {
        id: props.projectId.toString(),
        inspectionId: inspection.id.toString(),
      }
    })


  } finally {
    reset();
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
