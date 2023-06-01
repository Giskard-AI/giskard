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
                      :items="testSuites"
                      :item-text="'name'"
                      :item-value="'id'"
                      dense
                      hide-details
                  ></v-select>
                </ValidationProvider>
                <p class="text-h6 pt-4">Inputs</p>
                <SuiteInputListSelector
                        :editing="true"
                        :project-id="projectId"
                        :inputs="inputs"
                        :model-value="testInputs"/>
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
import {SuiteTestDTO, TestFunctionDTO, TestInputDTO, TestSuiteDTO} from '@/generated-sources';
import SuiteInputListSelector from '@/components/SuiteInputListSelector.vue';
import {chain} from 'lodash';

const {projectId, test, suiteId, testArguments} = defineProps<{
  projectId: number,
  test: TestFunctionDTO,
  suiteId?: number,
  testArguments: { [name: string]: string }
}>();

const dialog = ref<boolean>(false);
const testSuites = ref<TestSuiteDTO[]>([]);
const selectedSuite = ref<number | null>(null);
const testInputs = ref<{ [name: string]: TestInputDTO }>({});

onMounted(() => loadData());

async function loadData() {
  testSuites.value = await api.getTestSuites(projectId);
  selectedSuite.value = testSuites.value.find(({id}) => id === suiteId)?.id ?? null
  testInputs.value = test.args.reduce((result, arg) => {
    result[arg.name] = {
      name: arg.name,
      type: arg.type,
      isAlias: false,
      value: testArguments[arg.name] ?? ''
    }
    return result
  }, {} as { [name: string]: TestInputDTO })
}


const inputs = computed(() =>
    chain(test.args)
        .keyBy('name')
        .mapValues('type')
        .value()
);

async function submit(close) {
  const suiteTest: SuiteTestDTO = {
    testUuid: test.uuid,
    testInputs: chain(testInputs.value)
        .omitBy(({value}) => value === null
            || (typeof value === 'string' && value.trim() === '')
            || (typeof value === 'number' && Number.isNaN(value)))
        .value() as { [name: string]: TestInputDTO }
  }

  await api.addTestToSuite(projectId, selectedSuite.value!, suiteTest);
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
