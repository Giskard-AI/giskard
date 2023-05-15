<template>
  <v-list-item-group>
    <template v-for="({result, suiteTest}) in props.tests">
      <v-divider/>
      <v-list-item :value="result" @click="testInfo(suiteTest)">
        <v-list-item-icon>
          <v-icon :color="getColor(result)" size="40">{{
              getIcon(result)
            }}
          </v-icon>
        </v-list-item-icon>
        <v-list-item-content>
          <v-list-item-title>
            <div class="d-flex justify-space-between">
              <span>{{ getTestName(suiteTest.test) }}</span>
              <div>
                <v-btn
                    v-if="result !== undefined && !result.passed"
                    text
                    color="green"
                    @click.stop="debugTest(result, suiteTest)"
                >
                  <v-icon>mdi-bug</v-icon>
                  Debug
                </v-btn>
                <v-btn
                    v-if="!compact"
                    text
                    icon
                    color="error"
                    @click.stop="removeTest(suiteTest)"
                >
                  <v-icon>delete</v-icon>
                </v-btn>
              </div>
            </div>
          </v-list-item-title>
          <v-list-item-subtitle v-if="compact">
            {{ result ? `Metric : ${result.metric}` : "Not executed" }}
          </v-list-item-subtitle>
          <v-list-item-subtitle v-else>
            {{ result ? `Metric : ${result.metric}` : "Not executed" }}<br/>
            UUID: {{ suiteTest.test.uuid }}
          </v-list-item-subtitle>
        </v-list-item-content>
      </v-list-item>
    </template>
  </v-list-item-group>
</template>

<script setup lang="ts">

import {storeToRefs} from 'pinia';
import {useTestSuiteStore} from '@/stores/test-suite';
import {SuiteTestDTO, SuiteTestExecutionDTO, TestFunctionDTO, TestSuiteExecutionDTO} from '@/generated-sources';
import {Colors} from '@/utils/colors';
import {$vfm} from 'vue-final-modal';
import SuiteTestInfoModal from '@/views/main/project/modals/SuiteTestInfoModal.vue';
import {api} from '@/api';
import ConfirmModal from "@/views/main/project/modals/ConfirmModal.vue";
import {useRouter} from "vue-router/composables";

const props = withDefaults(defineProps<{
  tests: {
    suiteTest: SuiteTestDTO,
    result?: SuiteTestExecutionDTO
  }[],
  compact: boolean,
  execution: TestSuiteExecutionDTO
}>(), {
  compact: false
});

const testSuiteStore = useTestSuiteStore();
const {suite} = storeToRefs(testSuiteStore);

const router = useRouter();


function getTestName(test: TestFunctionDTO) {
  const name = test.displayName ?? test.name;

  if (props.compact) {
    return name;
  }

  const tags = test.tags.filter(tag => tag !== 'giskard' && tag !== 'pickle');


  if (tags.length === 0) {
    return name;
  } else {
    return tags.reduce((list, tag) => `${list} #${tag}`, '') + ` (${name})`;
  }
}

function getColor(result?: SuiteTestExecutionDTO): string {
  if (result === undefined) {
    return 'grey';
  } else if (result.passed) {
    return Colors.PASS;
  } else {
    return Colors.FAIL;
  }
}

function getIcon(result?: SuiteTestExecutionDTO): string {
  if (result === undefined) {
    return 'block';
  } else if (result.passed) {
    return 'done';
  } else {
    return 'close';
  }
}

async function testInfo(suiteTest: SuiteTestDTO) {
  await $vfm.show({
    component: SuiteTestInfoModal,
    bind: {
      suiteTest
    }
  });
}

async function removeTest(suiteTest: SuiteTestDTO) {
  await $vfm.show({
    component: ConfirmModal,
    bind: {
      title: 'Remove test',
      text: `Are you sure that you want to remove this test from the test suite?`,
      isWarning: true
    },
    on: {
      async confirm(close) {
        await api.removeTest(suite.value!.projectKey!, suite.value!.id!, suiteTest.id!);
        await testSuiteStore.reload();
        close();
      }
    }
  });
}

async function debugTest(result: SuiteTestExecutionDTO, suiteTest: SuiteTestDTO) {

  let model = props.execution.inputs.filter(input => input.name === 'model')[0].value;

  let res = await api.runAdHocTest(testSuiteStore.projectId!, suiteTest.testUuid, props.execution.inputs, true);

  let dataset = res.result[0].result.outputDfUuid;

  const debuggingSession = await api.prepareInspection({
    datasetId: dataset,
    modelId: model as string,
    name: "Debugging session ..."
  });

  await router.push({
    name: 'inspection',
    params: {
      projectId: testSuiteStore.projectId!,
      inspectionId: debuggingSession.id
    }
  });
}
</script>

