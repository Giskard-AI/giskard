<template>
  <v-container>
    <div class="d-flex">
      <v-icon
          :color="!props.execution ? 'grey' : props.execution.result === TestResult.PASSED ? Colors.PASS : Colors.FAIL"
          size="64">{{
          testResultIcon
        }}
      </v-icon>
      <div>
        <h2>

          Test Suite
        </h2>
        <h4
            v-if="!props.execution">No execution has been performed yet!</h4>
        <h4
            v-else-if="props.execution.result === TestResult.ERROR">An error arose during the execution</h4>
        <h4 v-else-if="filteredTest.length === 0">No test match the current filter</h4>
        <h4 v-else-if="executedTests.length > 0" :style="{
          color: successColor
        } ">Success ratio: {{ successRatio.passed }} /
          {{ successRatio.executed }}</h4>
      </div>
      <div class="flex-grow-1"/>
      <v-btn icon @click="openLogs" color="secondary">
        <v-icon>text_snippet</v-icon>
      </v-btn>
      <v-btn icon @click="openSettings" color="secondary">
        <v-icon>settings</v-icon>
      </v-btn>
    </div>

    <div class="d-flex mt-4 mb-4">
      <v-select
          v-model="statusFilter"
          label="Status"
          :items="statusFilterOptions"
          item-text="label"
          variant="underlined"
          hide-details="auto"
          dense
          class="mr-4"
      >
      </v-select>
      <v-text-field v-model="searchFilter" append-icon="search"
                    label="Search" type="text" dense></v-text-field>
    </div>
    <SuiteTestExecutionList :tests="filteredTest"/>
  </v-container>
</template>

<script setup lang="ts">

import {storeToRefs} from 'pinia';
import {useTestSuiteStore} from '@/stores/test-suite';
import {TestResult, TestSuiteExecutionDTO} from '@/generated-sources';
import {Colors, pickHexLinear, rgbToHex, SUCCESS_GRADIENT} from '@/utils/colors';
import {computed, onMounted, ref, watch} from 'vue';
import {chain} from 'lodash';
import {$vfm} from 'vue-final-modal';
import ExecutionLogsModal from '@/views/main/project/modals/ExecutionLogsModal.vue';
import {api} from '@/api';
import CreateTestSuiteModal from '@/views/main/project/modals/CreateTestSuiteModal.vue';
import {useTestSuiteCompareStore} from '@/stores/test-suite-compare';
import SuiteTestExecutionList from '@/views/main/project/SuiteTestExecutionList.vue';

const props = defineProps<{ execution?: TestSuiteExecutionDTO }>();

const testSuiteStore = useTestSuiteStore();
const {registry, models, datasets, inputs, suite, projectId} = storeToRefs(testSuiteStore);
const testSuiteCompareStore = useTestSuiteCompareStore();

onMounted(() => {
  testSuiteCompareStore.setCurrentExecution(props.execution ? props.execution.id : null);
})

watch(() => props.execution,
    () => testSuiteCompareStore.setCurrentExecution(props.execution ? props.execution.id : null),
    {deep: true});

const statusFilterOptions = [{
  label: 'All',
  filter: (_) => true
}, {
  label: 'Passed',
  filter: (result) => result !== undefined && result.passed
}, {
  label: 'Failed',
  filter: (result) => result !== undefined && !result.passed
}, {
  label: 'Not executed',
  filter: (result) => result === undefined
}];

const statusFilter = ref<string>(statusFilterOptions[0].label);
const searchFilter = ref<string>("");

const testResultIcon = computed(() => {
  if (!props.execution) {
    return 'block'
  }
  switch (props.execution.result) {
    case TestResult.PASSED:
      return 'done';
    case TestResult.FAILED:
      return 'close';
    default:
      return 'error';
  }
})


const registryByUuid = computed(() => chain(registry.value).keyBy('uuid').value());

const filteredTest = computed(() => suite.value === null ? [] : chain(suite.value!.tests)
    .map(suiteTest => ({
      suiteTest,
      test: registryByUuid.value[suiteTest.testUuid],
      result: props.execution?.results?.find(result => result.test.id === suiteTest.id)
    }))
    .filter(({result}) => statusFilterOptions.find(opt => statusFilter.value === opt.label)!.filter(result))
    .filter(({test}) => {
      const keywords = searchFilter.value.split(' ')
          .map(keyword => keyword.trim().toLowerCase())
          .filter(keyword => keyword !== '');
      return keywords.filter(keyword =>
          test.name.toLowerCase().includes(keyword)
          || test.doc?.toLowerCase()?.includes(keyword)
          || test.displayName?.toLowerCase()?.includes(keyword)
      ).length === keywords.length;
    })
    .value()
);

async function openSettings() {
  const project = await api.getProject(projectId.value!)
  $vfm.show({
    component: CreateTestSuiteModal,
    bind: {
      projectKey: project.key,
      projectId: project.id,
      suite: suite.value
    }
  });
}

function openLogs() {
  $vfm.show({
    component: ExecutionLogsModal,
    bind: {
      logs: props.execution?.logs
    }
  });
}

const executedTests = computed(() => !props.execution || props.execution.result === TestResult.ERROR ? []
    : filteredTest.value.filter(({result}) => result !== undefined));

const successRatio = computed(() => ({
  passed: executedTests.value.filter(({result}) => result!.passed).length,
  executed: executedTests.value.length
}))

const successColor = computed(() => successRatio.value.executed === 0 ? Colors.PASS :
    rgbToHex(pickHexLinear(SUCCESS_GRADIENT, successRatio.value.passed / successRatio.value.executed)));
</script>

<style scoped lang="scss">
.log-viewer {
  overflow: auto;
  max-height: 400px;
}
</style>

