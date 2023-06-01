<template>
  <div>
    <vue-final-modal
        v-slot="{ close }"
        v-bind="$attrs"
        classes="modal-container"
        content-class="modal-content"
        v-on="$listeners"
    >
      <div class="text-center">

        <v-card>
          <v-card-title>
            Configure run parameters
          </v-card-title>

          <v-card-text>
            <div v-for="(input, idx) of testSuiteInputs">
              <h2 v-if="testSuiteInputs.length > 1">Execution {{ idx + 1 }}
                <v-btn icon v-if="idx > 1"
                       @click="() => {testSuiteInputs.splice(idx, 1)}"
                       color="error">
                  <v-icon>delete</v-icon>
                </v-btn>
              </h2>
              <TestInputListSelector
                  editing
                  :model-value="input"
                  :inputs="props.inputs"
                  :project-id="props.projectId"
              />
            </div>
            <v-btn v-if="testSuiteInputs.length > 1"
                   @click="() => testSuiteInputs = [...testSuiteInputs, createInputs()]">
              <v-icon>add</v-icon>
              Add an execution
            </v-btn>
          </v-card-text>

          <v-divider></v-divider>

          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn
                color="primary"
                text
                @click="executeTestSuite(close)"
                :disabled="!isAllParamsSet() || running"
            >
              <v-icon>arrow_right</v-icon>
              Run test suite
            </v-btn>
          </v-card-actions>
        </v-card>
      </div>
    </vue-final-modal>
  </div>
</template>

<script setup lang="ts">

import {computed, onMounted, ref} from 'vue';
import {api} from '@/api';
import mixpanel from 'mixpanel-browser';
import TestInputListSelector from '@/components/TestInputListSelector.vue';
import {useMainStore} from "@/stores/main";
import {useTestSuiteStore} from '@/stores/test-suite';
import {TestInputDTO} from '@/generated-sources';
import {useRouter} from 'vue-router/composables';

const props = defineProps<{
  projectId: number,
  suiteId: number,
  inputs: { [name: string]: string },
  compareMode: boolean
}>();

const mainStore = useMainStore();
const testSuiteStore = useTestSuiteStore();

const running = ref<boolean>(false);


const testSuiteInputs = ref<{
  [name: string]: TestInputDTO
}[]>([]);


const inputs = computed(() => Object.keys(props.inputs).map((name) => ({
  name,
  type: props.inputs[name]
})));


function createInputs() {
  return Object.entries(props.inputs).reduce((result, [name, type]) => {
    result[name] = {
      isAlias: false,
      name,
      type,
      value: ''
    }
    return result;
  }, {});
}

onMounted(() => {
  testSuiteInputs.value = props.compareMode ? [createInputs(), createInputs()] : [createInputs()];
})

function isAllParamsSet() {
  return testSuiteInputs.value.filter(inputs => Object.keys(props.inputs)
      .map(name => inputs[name])
      .findIndex(param => param && (param.value === null || param.value.trim() === '')) !== -1)
      .length === 0;
}

const router = useRouter();

async function executeTestSuite(close) {
  mixpanel.track('Run test suite', {suiteId: props.suiteId});
  running.value = true;

  try {
    const jobUuids = await Promise.all(testSuiteInputs.value.map(input => {
      new Promise<Promise<void>>((resolve, reject) => {
        api.executeTestSuite(props.projectId, props.suiteId, Object.values(input)
            .reduce((result, input) => {
              result[input.name] = input.value;
              return result;
            }, {}))
            .then(jobUuid => {
              resolve(testSuiteStore.trackJob(jobUuid));
            })
            .catch(err => reject(err));
      })
    }));

    if (props.compareMode) {
      await Promise.all(jobUuids);
      router.push({name: 'test-suite-compare-executions', query: {latestCount: jobUuids.length.toString()}})
    } else {
      mainStore.addNotification({content: 'Test suite execution has been scheduled', color: 'success'});
    }
    // Track job asynchronously
  } finally {
    running.value = false;
    close();
  }

}
</script>

<style scoped>
::v-deep(.modal-container) {
  display: flex;
  justify-content: center;
  align-items: center;
}

::v-deep(.modal-content) {
  position: relative;
  display: flex;
  flex-direction: column;
  margin: 0 1rem;
  padding: 1rem;
  min-width: 50vw;
}

</style>
