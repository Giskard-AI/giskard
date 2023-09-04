<template>
  <vue-final-modal v-slot="{ close }" v-bind="$attrs" classes="modal-container" content-class="modal-content" v-on="$listeners">
    <v-form @submit.prevent="">
      <ValidationObserver ref="observer" v-slot="{ invalid }">
        <v-card>
          <v-card-title>
            {{ suite ? `Edit ${suite?.name}` : "Create a new test suite" }}
          </v-card-title>

          <v-card-text>
            <v-row>
              <v-col cols=12>
                <ValidationProvider name="test suite name" rules="required" v-slot="{ errors }">
                  <v-text-field label="Test suite name" autofocus v-model="name" :error-messages="errors" outlined></v-text-field>
                </ValidationProvider>
                <h2 v-if="showAdvancedSettings">Inputs</h2>
                <v-simple-table>
                  <template v-slot:default>
                    <thead>
                      <tr>
                        <th class="text-left" id="input-name">
                          Input name
                        </th>
                        <th class="text-left" id="input-type">
                          Input type
                        </th>
                        <th id="input-options"></th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(input, index) in suiteInputs" :key="index">
                        <td>
                          <ValidationProvider name="input name" rules="required" v-slot="{ errors }">
                            <v-text-field v-model="input.name" :error-messages="errors"></v-text-field>
                          </ValidationProvider>
                        </td>
                        <td>
                          <v-select v-model="input.type" :items="availableTypes"></v-select>
                        </td>
                        <td>
                          <v-btn icon @click="() => handleInputSettingsClick(input)" v-if="['BaseModel', 'Dataset'].indexOf(input.type) !== -1">
                            <v-icon>settings</v-icon>
                          </v-btn>
                          <v-btn icon @click="() => suiteInputs.splice(index, 1)">
                            <v-icon color="accent">delete</v-icon>
                          </v-btn>
                        </td>
                      </tr>
                    </tbody>
                  </template>
                </v-simple-table>
                <div class="d-flex flex-column align-end pt-4">
                  <v-btn @click="() => suiteInputs.push({ name: '', type: availableTypes[0], suiteInputType: 'suite' })">
                    <v-icon>add</v-icon>
                    Add input
                  </v-btn>
                  <v-btn v-if="!showAdvancedSettings" class="mt-4" text @click="() => showAdvancedSettings = true">
                    <v-icon>add_link</v-icon>
                    {{ sharedSuiteInputs.length === 0 ? 'Create' : 'Update' }} shared inputs
                  </v-btn>
                </div>
                <h2 v-if="showAdvancedSettings">Shared inputs</h2>
                <v-simple-table v-if="showAdvancedSettings">
                  <template v-slot:default>
                    <thead>
                      <tr>
                        <th class="text-left" id="input-name">
                          Input name
                        </th>
                        <th class="text-left" id="input-type">
                          Input type
                        </th>
                        <th class="text-left" id="input-type">
                          Input value
                        </th>
                        <th id="input-options"></th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(input, index) in sharedSuiteInputs" :key="index">
                        <td>
                          <ValidationProvider name="input name" rules="required" v-slot="{ errors }">
                            <v-text-field v-model="input.name" :error-messages="errors"></v-text-field>
                          </ValidationProvider>
                        </td>
                        <td>
                          <v-select v-model="input.type" :items="availableTypes"></v-select>
                        </td>
                        <td>
                          <DatasetSelector :project-id="projectId" :label="input.name" :return-object="false" v-if="input.type === 'Dataset'" :value.sync="input.value" />
                          <ModelSelector :project-id="projectId" :label="input.name" :return-object="false" v-else-if="input.type === 'BaseModel'" :value.sync="input.value" />
                          <v-text-field :step='input.type === "float" ? 0.1 : 1' v-model="input.value" v-else-if="['float', 'int'].includes(input.type)" hide-details single-line type="number" outlined dense />
                        </td>
                        <td>
                          <v-btn icon @click="() => sharedSuiteInputs.splice(index, 1)">
                            <v-icon color="accent">delete</v-icon>
                          </v-btn>
                        </td>
                      </tr>
                    </tbody>
                  </template>
                </v-simple-table>
                <div v-if="showAdvancedSettings" class="d-flex flex-row-reverse pt-4">
                  <v-btn @click="() => sharedSuiteInputs.push({ name: '', type: availableTypes[0], value: null, isAlias: false })">
                    <v-icon>add</v-icon>
                    Add shared input
                  </v-btn>
                </div>
              </v-col>
            </v-row>
          </v-card-text>

          <v-divider></v-divider>

          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="primary" text @click="submit(close)" :disabled="invalid" :loading="isLoading">
              {{ suite ? 'Update' : 'Create' }}
            </v-btn>
          </v-card-actions>
        </v-card>
      </ValidationObserver>
    </v-form>
  </vue-final-modal>
</template>

<script setup lang="ts">

import { onMounted, ref } from 'vue';
import mixpanel from 'mixpanel-browser';
import { api } from '@/api';
import { FunctionInputDTO, GenerateTestSuiteDTO, GenerateTestSuiteInputDTO, TestSuiteDTO } from '@/generated-sources';
import { useRouter } from 'vue-router';
import { $vfm } from 'vue-final-modal';
import InputSettingsModal from '@/views/main/project/modals/ModelInputSettingsModal.vue';
import { useTestSuiteStore } from '@/stores/test-suite';
import DatasetSelector from '@/views/main/utils/DatasetSelector.vue';
import ModelSelector from '@/views/main/utils/ModelSelector.vue';

const { projectKey, projectId, suite } = defineProps<{
  projectKey: string,
  projectId: number
  suite?: TestSuiteDTO
}>();

const dialog = ref<boolean>(false);
const name = ref<string>('');
const suiteInputs = ref<GenerateTestSuiteInputDTO[]>([]);
const sharedSuiteInputs = ref<FunctionInputDTO[]>([]);
const isLoading = ref<boolean>(false);
const showAdvancedSettings = ref<boolean>(false);

const router = useRouter();
const { updateTestSuite } = useTestSuiteStore();

onMounted(() => {
  if (suite) {
    name.value = suite.name;
    sharedSuiteInputs.value = [...suite.testInputs];
  }
})

const availableTypes = ['BaseModel', 'Dataset', 'str', 'bool', 'int', 'float']

async function submit(close) {
  isLoading.value = true;

  if (suite) {
    await updateTestSuite(projectKey, {
      ...suite,
      name: name.value,
      testInputs: sharedSuiteInputs.value
    }).finally(() => isLoading.value = false);
  } else {
    mixpanel.track('Create test suite v2', {
      projectKey
    });

    const createdTestSuiteId = await api.generateTestSuite(projectKey, {
      name: name.value,
      inputs: suiteInputs.value,
      sharedInputs: sharedSuiteInputs.value
    } as GenerateTestSuiteDTO)
      .finally(() => isLoading.value = false);

    await router.push({ name: 'project-testing-test-suite-overview', params: { suiteId: createdTestSuiteId.toString() } });
  }

  dialog.value = false;

  close();
}

function handleInputSettingsClick(input: GenerateTestSuiteInputDTO) {
  $vfm.show({
    component: InputSettingsModal,
    bind: {
      input
    },
    on: {
      async save(meta) {
        Object.assign(input, meta);
      }
    }
  });
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
