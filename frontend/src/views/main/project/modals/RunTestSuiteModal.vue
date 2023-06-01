<template>
  <div>
    <v-dialog
        v-model="dialog"
        width="650"
    >
      <template v-slot:activator="{ on, attrs }">
        <v-btn tile class='mx-1' @click='openPopup'
               :loading='running'
               :disabled='running'
               v-bind="attrs"
               color="primary"
               v-on="on">
          <v-icon>arrow_right</v-icon>
          Run test suite
        </v-btn>
      </template>

      <v-card>
        <v-card-title>
          Configure run parameters
        </v-card-title>

        <v-card-text>
          <TestInputListSelector
              editing
              :model-value="testSuiteInputs"
              :inputs="props.inputs"
              :project-id="props.projectId"
          />
        </v-card-text>

        <v-divider></v-divider>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
              color="primary"
              text
              @click="executeTestSuite()"
              :disabled="!isAllParamsSet() || running"
          >
            <v-icon>arrow_right</v-icon>
            Run test suite
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">

import {computed, ref} from 'vue';
import {api} from '@/api';
import mixpanel from 'mixpanel-browser';
import TestInputListSelector from '@/components/TestInputListSelector.vue';
import {useMainStore} from "@/stores/main";
import {useTestSuiteStore} from '@/stores/test-suite';
import {TestInputDTO} from '@/generated-sources';

const props = defineProps<{
  projectId: number,
  suiteId: number,
  inputs: { [name: string]: string }
}>();

const mainStore = useMainStore();
const testSuiteStore = useTestSuiteStore();

const dialog = ref<boolean>(false);
const running = ref<boolean>(false);

const testSuiteInputs = ref<{
  [name: string]: TestInputDTO
}>({});


const inputs = computed(() => Object.keys(props.inputs).map((name) => ({
  name,
  type: props.inputs[name]
})));

function isAllParamsSet() {
  return Object.keys(props.inputs)
      .map(name => testSuiteInputs.value[name])
      .findIndex(param => param && (param.value === null || param.value.trim() === '')) === -1;
}


function openPopup() {
  if (Object.keys(props.inputs).length === 0) {
    executeTestSuite();
  } else {
    testSuiteInputs.value = Object.entries(props.inputs).reduce((result, [name, type]) => {
      result[name] = {
        isAlias: false,
        name,
        type,
        value: ''
      }
      return result;
    }, {});
    dialog.value = true;
  }
}

async function executeTestSuite() {
  mixpanel.track('Run test suite', {suiteId: props.suiteId});
  running.value = true;

  try {
    const jobUuid = await api.executeTestSuite(props.projectId, props.suiteId, Object.values(testSuiteInputs.value)
        .reduce((result, input) => {
          result[input.name] = input.value;
          return result;
        }, {}));
    mainStore.addNotification({content: 'Test suite execution has been scheduled', color: 'success'});
    // Track job asynchronously
    testSuiteStore.trackJob(jobUuid);
  } finally {
    running.value = false;
    dialog.value = false;
  }

}
</script>
