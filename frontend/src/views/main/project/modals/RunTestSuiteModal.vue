<template>
  <div>
    <v-dialog
        v-model="dialog"
        width="650"
    >
      <template v-slot:activator="{ on, attrs }">
        <v-btn small tile class='mx-1' @click='openPopup'
               :loading='running'
               :disabled='running'
               v-bind="attrs"
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
import {commitAddNotification} from '@/store/main/mutations';
import store from '@/store';
import TestInputListSelector from '@/components/TestInputListSelector.vue';

const props = defineProps<{
  projectId: number,
  suiteId: number,
  inputs: { [name: string]: string }
}>();

const emit = defineEmits(['uuid']);

const dialog = ref<boolean>(false);
const running = ref<boolean>(false);

const testSuiteInputs = ref<{
  [name: string]: any
}>({});

const inputs = computed(() => Object.keys(props.inputs).map((name) => ({
  name,
  type: props.inputs[name]
})));

function isAllParamsSet() {
  return Object.keys(props.inputs)
      .map(name => testSuiteInputs.value[name])
      .findIndex(param => param === null || param === undefined) === -1;
}


function openPopup() {
  if (Object.keys(props.inputs).length === 0) {
    executeTestSuite();
  } else {
    testSuiteInputs.value = {};
    dialog.value = true;
  }
}

async function executeTestSuite() {
  mixpanel.track('Run test suite', {suiteId: props.suiteId});
  running.value = true;

  try {
    const jobUuid = await api.executeTestSuiteNew(props.projectId, props.suiteId, testSuiteInputs.value);
    commitAddNotification(store, {content: 'Test suite execution has been scheduled', color: 'success'});
    emit('uuid', jobUuid);
  } finally {
    running.value = false;
    dialog.value = false;
  }

}
</script>
