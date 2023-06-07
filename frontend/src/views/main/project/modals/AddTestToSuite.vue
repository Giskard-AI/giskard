<template>
  <vue-final-modal v-slot="{ close }" v-bind="$attrs" classes="modal-container" content-class="modal-content" v-on="$listeners">
    <v-form @submit.prevent="">
      <ValidationObserver ref="observer" v-slot="{ invalid }">
        <v-card class="modal-card">
          <v-card-title>
            Add {{ test.name }} to a test suite
          </v-card-title>

          <v-card-text>
            <v-row>
              <v-col cols=12>
                <ValidationProvider name="Test suite" mode="eager" rules="required" v-slot="{ errors }">
                  <v-select outlined label="Test suite" v-model="selectedSuite" :items="testSuites" :item-text="'name'" :item-value="'id'" dense hide-details>
                    <template v-slot:append-item>
                      <v-divider></v-divider>
                      <v-list-item link @click="createTestSuite" class="pt-1">
                        <v-list-item-avatar color="grey lighten-4" class="my-1 mr-2" style="height: 25px;min-width: 25px;width: 25px;">
                          <v-icon small>
                            mdi-plus
                          </v-icon>
                        </v-list-item-avatar>
                        <v-list-item-content>
                          <v-list-item-title>
                            Add new test suite
                          </v-list-item-title>
                        </v-list-item-content>
                      </v-list-item>
                    </template>
                  </v-select>
                </ValidationProvider>
                <p class="text-h6 pt-4">Fixed inputs</p>
                <p>Specify inputs that will be constant during each execution of the test.<br />
                  The inputs left blank will have to be provided at test execution time.</p>
                <SuiteInputListSelector class="pt-4" :editing="true" :project-id="projectId" :inputs="inputs" :model-value="testInputs" :doc="doc" />
              </v-col>
            </v-row>
          </v-card-text>

          <v-divider></v-divider>

          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="primary" text @click="submit(close)" :disabled="invalid">
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
import {FunctionInputDTO, SuiteTestDTO, TestFunctionDTO, TestSuiteDTO} from '@/generated-sources';
import SuiteInputListSelector from '@/components/SuiteInputListSelector.vue';
import {chain} from 'lodash';
import {useMainStore} from "@/stores/main";
import {TYPE} from 'vue-toastification';
import {extractArgumentDocumentation, ParsedDocstring} from "@/utils/python-doc.utils";
import mixpanel from 'mixpanel-browser';
import {anonymize} from "@/utils";

const {projectId, test, suiteId, testArguments} = defineProps<{
  projectId: number,
  test: TestFunctionDTO,
  suiteId?: number,
  testArguments: { [name: string]: FunctionInputDTO }
}>();

const dialog = ref<boolean>(false);
const testSuites = ref<TestSuiteDTO[]>([]);
const selectedSuite = ref<number | null>(null);
const testInputs = ref<{ [name: string]: FunctionInputDTO }>({});
const doc = ref<ParsedDocstring | null>(null);

onMounted(() => loadData());

async function loadData() {
  doc.value = extractArgumentDocumentation(test)
  testSuites.value = await api.getTestSuites(projectId);
  selectedSuite.value = testSuites.value.find(({ id }) => id === suiteId)?.id ?? null
  testInputs.value = test.args.reduce((result, arg) => {
    result[arg.name] = testArguments[arg.name] ?? {
      name: arg.name,
      type: arg.type,
      isAlias: false,
      value: '',
      params: []
    }
    return result
  }, {} as { [name: string]: FunctionInputDTO })
  testInputs.value['model'].value = null;
  testInputs.value['dataset'].value = null;
}


const inputs = computed(() =>
  chain(test.args)
    .keyBy('name')
    .mapValues('type')
    .value()
);

const mainStore = useMainStore();

async function submit(close) {
  mixpanel.track("Add test to suite", {
    testName: test.name,
    suiteId: selectedSuite.value,
    inputs: anonymize(Object.values(testInputs.value))
  })

  const suiteTest: SuiteTestDTO = {
    test,
    testUuid: test.uuid,
    functionInputs: chain(testInputs.value)
        .omitBy(({value}) => value === null
            || (typeof value === 'string' && value.trim() === '')
            || (typeof value === 'number' && Number.isNaN(value)))
        .value() as { [name: string]: FunctionInputDTO }
  }

  await api.addTestToSuite(projectId, selectedSuite.value!, suiteTest);
  await mainStore.addNotification({
    content: `'${test.displayName ?? test.name}' has been added to '${testSuites.value.find(({id}) => id === selectedSuite.value)!.name}'`,
    color: TYPE.SUCCESS
  });
  close();

  mixpanel.track('Add test to test suite',
      {
        suiteId: selectedSuite.value,
        projectId: projectId,
        testUuid: test.uuid,
        testName: test.displayName ?? test.name
      });
}

async function createTestSuite() {
  const project = await api.getProject(projectId);


  const suite = await api.createTestSuite(project.key, {
    id: null,
    name: 'Unnamed test suite',
    projectKey: project.key,
    functionInputs: [],
    tests: []
  });

  mixpanel.track('Create test suite',
      {
        id: suite,
        projectKey: project.key,
        screen: 'Test catalog (Add test to suite modal)'
      });

  await loadData();

  selectedSuite.value = suite;
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
