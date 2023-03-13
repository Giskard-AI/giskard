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
        <v-card>
          <v-card-title>
            {{ suite ? `Edit ${suite?.name}` : "Create a new test suite" }}
          </v-card-title>

          <v-card-text>
            <v-row>
              <v-col cols=12>
                <ValidationProvider name="test suite name" rules="required" v-slot="{errors}">
                  <v-text-field label="Test suite name" autofocus v-model="name" :error-messages="errors"
                                outlined></v-text-field>
                </ValidationProvider>
                <v-simple-table>
                  <template v-slot:default>
                    <thead>
                    <tr>
                      <th class="text-left" id="input-name">
                        Name
                      </th>
                      <th class="text-left" id="input-type">
                        Type
                      </th>
                      <th id="input-options"></th>
                    </tr>
                    </thead>
                    <tbody>
                    <tr
                        v-for="(input, index) in suiteInputs"
                        :key="index"
                    >
                      <td>
                        <ValidationProvider name="input name" rules="required" v-slot="{errors}">
                          <v-text-field v-model="input.name" :error-messages="errors"></v-text-field>
                        </ValidationProvider>
                      </td>
                      <td>
                        <v-select
                            v-model="input.type"
                            :items="availableTypes"
                        ></v-select>
                      </td>
                      <td>
                        <v-btn icon @click="() => handleInputSettingsClick(input)"
                               v-if="['Model', 'Dataset'].indexOf(input.type) !== -1">
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
                <v-btn
                    @click="() => suiteInputs.push({name: '', type: availableTypes[0], suiteInputType: 'suite'})">
                  Add input
                </v-btn>
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
                :loading="isLoading"
            >
              {{ suite ? 'Update' : 'Create' }}
            </v-btn>
          </v-card-actions>
        </v-card>
      </ValidationObserver>
    </v-form>
  </vue-final-modal>
</template>

<script setup lang="ts">

import {onMounted, ref} from 'vue';
import mixpanel from 'mixpanel-browser';
import {api} from '@/api';
import {GenerateTestSuiteDTO, GenerateTestSuiteInputDTO, TestSuiteDTO} from '@/generated-sources';
import {useRouter} from 'vue-router/composables';
import {$vfm} from 'vue-final-modal';
import InputSettingsModal from '@/views/main/project/modals/ModelInputSettingsModal.vue';
import {useTestSuiteStore} from '@/stores/test-suite';

const {projectKey, projectId, suite} = defineProps<{
  projectKey: string,
  projectId: number
  suite?: TestSuiteDTO
}>();

const dialog = ref<boolean>(false);
const name = ref<string>('');
const suiteInputs = ref<GenerateTestSuiteInputDTO[]>([]);
const isLoading = ref<boolean>(false);

const router = useRouter();
const {updateTestSuite} = useTestSuiteStore();

onMounted(() => {
  if (suite) {
    name.value = suite.name;
  }
})

const availableTypes = ['Model', 'Dataset', 'str', 'bool', 'int', 'float']

async function submit(close) {
  isLoading.value = true;

  if (suite) {
    await updateTestSuite(projectKey, {
      ...suite,
      name: name.value
    }).finally(() => isLoading.value = false);
  } else {
    mixpanel.track('Create test suite v2', {
      projectKey
    });

    const createdTestSuiteId = await api.generateTestSuite(projectKey, {
      name: name.value,
      inputs: suiteInputs.value.map(val => ({...val}))
    } as GenerateTestSuiteDTO)
        .finally(() => isLoading.value = false);

    await router.push({name: 'test-suite-overview', params: {suiteId: createdTestSuiteId.toString()}});
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
