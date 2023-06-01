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
          <v-list>
            <v-list-item v-for="input in inputs" class="pl-0 pr-0">
              <v-row>
                <v-col>
                  <v-list-item-content>
                    <v-list-item-title>{{ input.name }}</v-list-item-title>
                    <v-list-item-subtitle class="text-caption">{{ input.type }}</v-list-item-subtitle>
                  </v-list-item-content>
                </v-col>
                <v-col>
                  <DatasetSelector :project-id="projectId" :label="input.name" :return-object="false"
                                   v-if="input.type === 'Dataset'" :value.sync="testSuiteInputs[input.name]"/>
                  <ModelSelector :project-id="projectId" :label="input.name" :return-object="false"
                                 v-if="input.type === 'Model'" :value.sync="testSuiteInputs[input.name]"/>
                  <v-text-field
                      :step='input.type === "float" ? 0.1 : 1'
                      v-model="testSuiteInputs[input.name]"
                      v-if="['float', 'int'].includes(input.type)"
                      hide-details
                      single-line
                      type="number"
                      outlined
                      dense
                  />
                </v-col>
              </v-row>
            </v-list-item>
          </v-list>
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
import DatasetSelector from '@/views/main/utils/DatasetSelector.vue';
import ModelSelector from '@/views/main/utils/ModelSelector.vue';
import {api} from '@/api';
import mixpanel from 'mixpanel-browser';
import {commitAddNotification} from '@/store/main/mutations';
import store from '@/store';

const props = defineProps<{
  projectId: number,
  suiteId: number,
  inputs: {
    [name: string]: string
  }
}>();

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
    await api.executeTestSuiteNew(props.projectId, props.suiteId, testSuiteInputs.value);
    commitAddNotification(store, {content: 'Test suite execution has been scheduled', color: 'success'});
    // TODO: Add UI to see job running in settings
  } finally {
    running.value = false;
    dialog.value = false;
  }

}
</script>
