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
            Create a new test suite
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
                      <th id="delete-input"></th>
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
                        <v-btn icon @click="() => suiteInputs.splice(index, 1)">
                          <v-icon color="accent">delete</v-icon>
                        </v-btn>
                      </td>
                    </tr>
                    </tbody>
                  </template>
                </v-simple-table>
                <v-btn
                    @click="() => suiteInputs.push({name: '', type: availableTypes[0]})">
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
              Create
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
import {GenerateTestSuiteDTO, GenerateTestSuiteInputDTO, TestCatalogDTO} from '@/generated-sources';
import {useRouter} from 'vue-router/composables';

const {projectKey, projectId} = defineProps<{
  projectKey: string,
  projectId: number
}>();

let registry = ref<TestCatalogDTO | null>(null);
const dialog = ref<boolean>(false);
const name = ref<string>('');
const suiteInputs = ref<GenerateTestSuiteInputDTO[]>([]);
const isLoading = ref<boolean>(false);

const router = useRouter();

const availableTypes = ['Model', 'Dataset', 'str', 'bool', 'int', 'float']

onMounted(async () => {
  registry.value = await api.getTestsCatalog(projectId);
});

async function submit(close) {
  isLoading.value = true;

  mixpanel.track('Create test suite v2', {
    projectKey
  });


  const createdTestSuiteId = await api.generateTestSuite(projectKey, {
    name: name.value,
    inputs: suiteInputs.value.map(val => ({...val, suiteInputType: 'suite'}))
  } as GenerateTestSuiteDTO)
      .finally(() => isLoading.value = false);

  dialog.value = false;
  await router.push({name: 'test-suite-new', params: {suiteId: createdTestSuiteId.toString()}});

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
  min-width: 50vw;
}

</style>
