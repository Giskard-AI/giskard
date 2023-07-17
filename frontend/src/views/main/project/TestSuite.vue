<template>
  <div class="vc pb-0 parent-container">
    <div class="vc">
      <v-container class="main-container vc pt-0">
        <div class="d-flex flex-wrap pl-3 pr-3">
          <h1 class="test-suite-name">{{ suiteName }}</h1>
          <div class="flex-grow-1"></div>
          <v-btn text @click.stop="redirectToTesting">
            <v-icon class="mr-2">mdi-arrow-left</v-icon>
            Back to all suites
          </v-btn>
          <v-btn text @click="() => openSettings()"> Edit test suite </v-btn>
          <v-btn v-if="hasTest" :to="{ name: 'project-catalog-tests', query: { suiteId: suiteId } }" class="mx-1" color="secondary" outlined>
            Add test
          </v-btn>
        </div>
        <v-tabs class="pl-3 pr-3 mt-2">
          <v-tab :to="{ name: 'project-testing-test-suite-overview' }">
            <v-icon class="mr-2">mdi-chart-bar</v-icon>
            <span class="tab-item-text">Report</span>
          </v-tab>
          <v-tab :to="{ name: 'project-testing-test-suite-executions' }">
            <v-icon class="mr-2">history</v-icon>
            <span class="tab-item-text">Past executions</span>
          </v-tab>
        </v-tabs>
        <v-row v-if="!hideHeader" class="mt-0 overview-container pl-3 pr-3 pb-3">
          <v-col>
            <div class="d-flex flex-wrap align-center">
              <v-select v-model="statusFilter" :items="statusFilterOptions" class="mr-4 max-w-150" dense hide-details="auto" item-text="label" label="Test execution status" outlined variant="underlined" @input="handleFilterChanged">
              </v-select>
              <v-text-field v-model="searchFilter" append-icon="search" class="max-w-250" dense hide-details="auto" label="Search test" outlined placeholder="Performance" type="text" @input="handleFilterChanged"></v-text-field>
              <div class="flex-grow-1"></div>
              <v-tooltip bottom>
                <template v-slot:activator="{ on, attrs }">
                  <div v-on="on">
                    <v-btn color="primary" disabled large text @click="openExportDialog">Export </v-btn>
                  </div>
                </template>
                <span>Coming soon</span>
              </v-tooltip>
              <v-btn v-if="hasTest && hasInput && !hasJobInProgress" class="mx-1" color="primary" large outlined @click="openRunTestSuite(true)">
                Compare
              </v-btn>
              <v-btn v-if="hasTest" :loading="hasJobInProgress" class="mx-1" color="primary" large @click="handleRunTestSuite">
                Run test suite
              </v-btn>
            </div>
          </v-col>
        </v-row>
        <v-row class="vc overview-container pl-3 mt-0">
          <v-col class="vc pb-0" cols="12">
            <router-view />
          </v-col>
        </v-row>
      </v-container>
    </div>

    <v-dialog v-model="displayWorkerInstructions" max-width="70vw" @click:outside="openWorkerInstructions = false">
      <v-card>
        <v-card-title class="py-6">
          <h2>ML Worker is not connected</h2>
        </v-card-title>
        <v-card-text>
          <StartWorkerInstructions></StartWorkerInstructions>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<script lang="ts" setup>
import { computed, onActivated, ref, watch } from 'vue';
import { statusFilterOptions, useTestSuiteStore } from '@/stores/test-suite';
import { storeToRefs } from 'pinia';
import { useRoute, useRouter } from 'vue-router/composables';
import { $vfm } from 'vue-final-modal';
import RunTestSuiteModal from '@/views/main/project/modals/RunTestSuiteModal.vue';
import { useCatalogStore } from '@/stores/catalog';
import EditTestSuiteModal from '@/views/main/project/modals/EditTestSuiteModal.vue';
import { api } from '@/api';
import { useTestSuitesStore } from '@/stores/test-suites';
import ExportTestModalVue from './modals/ExportTestModal.vue';
import { debounce } from 'lodash';
import mixpanel from 'mixpanel-browser';
import StartWorkerInstructions from '@/components/StartWorkerInstructions.vue';
import { state } from '@/socket';

const router = useRouter();
const route = useRoute();

const testSuitesStore = useTestSuitesStore();
const { loadTestSuites, runTestSuite } = useTestSuiteStore();
const { loadCatalog } = useCatalogStore();

const props = defineProps<{
  projectId: number;
  suiteId: number;
}>();

const { suite, inputs, executions, hasTest, hasInput, statusFilter, searchFilter, hasJobInProgress } = storeToRefs(useTestSuiteStore());

const openWorkerInstructions = ref(false);

const suiteName = computed(() => {
  if (!suite.value) return `Unnamed test suite`;
  return suite.value.name ? suite.value.name : `Unnamed test suite`;
});

const isMLWorkerConnected = computed(() => {
  return state.workerStatus.connected;
});

const displayWorkerInstructions = computed(() => !isMLWorkerConnected.value && openWorkerInstructions.value);

const hideHeader = computed(() => route.name === 'project-testing-test-suite-configuration');

async function loadData() {
  await loadTestSuites(props.projectId, props.suiteId);
  await loadCatalog(props.projectId);
}

async function openRunTestSuite(compareMode: boolean) {
  if (hasInput.value) {
    await $vfm.show({
      component: RunTestSuiteModal,
      bind: {
        projectId: props.projectId,
        suiteId: props.suiteId,
        inputs: inputs.value,
        compareMode,
        previousParams: executions.value.length === 0 ? {} : executions.value[0].inputs,
      },
    });
  } else {
    if (!isMLWorkerConnected.value) {
      openWorkerInstructions.value = true;
      return;
    } else {
      await runTestSuite([]);
    }
  }
}

async function openSettings() {
  const project = await api.getProject(props.projectId);
  $vfm.show({
    component: EditTestSuiteModal,
    bind: {
      projectKey: project.key,
      projectId: project.id,
      suite: suite.value,
    },
  });
}

async function redirectToTesting() {
  testSuitesStore.setCurrentTestSuiteId(null);
  await router.push({ name: 'project-testing' });
}

function openExportDialog() {
  $vfm.show({
    component: ExportTestModalVue,
  });
}

const handleFilterChanged = debounce(
  () =>
    mixpanel.track('Filter tests of test suite', {
      suiteId: props.suiteId,
      projectId: props.projectId,
      statusFilter: statusFilter.value,
      searchFilter: searchFilter.value,
    }),
  1000
);

function handleRunTestSuite() {
  openRunTestSuite(false);
}

watch(
  () => props.suiteId,
  () => loadData()
);

onActivated(() => loadData());
</script>

<style lang="scss" scoped>
.main-container {
  width: 100%;
  max-width: 100%;
  color: rgb(98, 98, 98);

  b {
    color: black;
  }
}

.parent-container {
  margin-left: -12px;
  margin-right: -12px;
}

.overview-container {
  background-color: #f5f5f5;
}

.test-suite-name {
  font-style: normal;
  font-weight: 700;
  font-size: 24px;
  line-height: 32px;

  color: #163a30;
}

.max-w-150 {
  max-width: 150px;
}

.max-w-250 {
  max-width: 250px;
}

.tab-item-text {
  font-style: normal;
  font-weight: 500;
  font-size: 0.875em;
  line-height: 17px;
  display: flex;
  align-items: flex-end;
  text-transform: uppercase;
  font-feature-settings: 'case' on, 'cpsp' on;
}
</style>