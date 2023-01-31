<template>
  <vue-final-modal
      v-slot="{ close }"
      v-bind="$attrs"
      classes="modal-container"
      content-class="modal-content"
      v-on="$listeners"
  >
    <v-form @submit.prevent="">
      <ValidationObserver ref="observer" v-slot="{ invalid }">
        <v-card class="modal-card">
          <v-card-title>
            Add {{ test.name }} to a test suite
          </v-card-title>

          <v-card-text>
            <v-row>
              <v-col cols=12>
                <ValidationProvider name="Tes suite" mode="eager" rules="required" v-slot="{errors}">
                  <v-select
                      outlined
                      label="Test suite"
                      v-model="selectedSuite"
                      :items="testSuitesWithoutTest"
                      :item-text="'name'"
                      :item-value="'id'"
                      dense
                      hide-details
                  ></v-select>
                </ValidationProvider>
                <p class="text-h6 pt-4">Inputs</p>
                <TestInputListSelector
                    :project-id="projectId"
                    :inputs="inputs"
                    :model-value="testInputs" />
              </v-col>
            </v-row>
          </v-card-text>

          <v-divider></v-divider>

          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn
                color="primary"
                text
                @click="submit(close)"
                :disabled="invalid"
            >
              Add to suite
            </v-btn>
          </v-card-actions>
        </v-card>
      </ValidationObserver>
    </v-form>
  </vue-final-modal>
</template>

<script setup lang="ts">

import {computed, onMounted, ref} from 'vue';
import {api} from '@/api';
import {SuiteTestDTO, TestDefinitionDTO, TestSuiteNewDTO} from '@/generated-sources';
import TestInputListSelector from '@/components/TestInputListSelector.vue';
import {chain, isNull} from 'lodash';

const { projectId, test } = defineProps<{
  projectId: number,
  test: TestDefinitionDTO
}>();

const dialog = ref<boolean>(false);
const testSuites = ref<TestSuiteNewDTO[]>([]);
const selectedSuite = ref<TestSuiteNewDTO | null>(null);
const testInputs = ref<{ [name: string]: any }>({});

onMounted(() => loadData());

async function loadData() {
  testSuites.value = await api.getTestSuitesNew(projectId);
}

const testSuitesWithoutTest = computed(() =>
  testSuites.value.filter(suite => suite.tests.findIndex(t => t.testId === test.id) === -1)
);

const inputs = computed(() =>
    chain(test.arguments)
        .keyBy('name')
        .mapValues('type')
        .value()
);

async function submit(close) {
  const suiteTest: SuiteTestDTO = {
    testId: test.id,
    testInputs: chain(testInputs.value)
        .omitBy(isNull)
        .mapValues((value, name) => ({
            name,
            value,
            isAlias: false
          }))
        .value()
  }

  await api.addTestToSuite(projectId, selectedSuite.value, suiteTest);
  close();
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
}

.modal-card {
  min-width: 50vw;
}
</style>
