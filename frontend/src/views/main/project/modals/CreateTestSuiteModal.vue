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
                      <th class="text-left">
                        Name
                      </th>
                      <th class="text-left">
                        Type
                      </th>
                      <th class="text-left">
                        Value
                      </th>
                      <th></th>
                    </tr>
                    </thead>
                    <tbody>
                    <tr
                        v-for="(input, index) in suiteInputs"
                        :key="index"
                    >
                      <td>
                        <v-select
                            v-model="input.name"
                            :items="[input.name, ...availableArguments]"
                        ></v-select>
                      </td>
                      <td>
                        <span v-if="typesByName[input.name].length === 1">{{ input.type }}</span>
                        <v-select v-else
                                  v-model="input.type"
                                  :items="typesByName[input.name]"
                        ></v-select>
                      </td>
                      <td>
                        <DatasetSelector :project-id="projectId" :label="input.name" :return-object="false"
                                         v-if="input.type === 'Dataset'" :value.sync="input.value"/>
                        <ModelSelector :project-id="projectId" :label="input.name" :return-object="false"
                                       v-else-if="input.type === 'Model'" :value.sync="input.value"/>
                        <v-text-field
                            :step='input.type === "float" ? 0.1 : 1'
                            v-model="input.value"
                            v-else-if="['float', 'int'].includes(input.type)"
                            hide-details
                            single-line
                            type="number"
                            outlined
                            dense
                        />
                        <v-text-field
                            v-model="input.value"
                            v-else-if="'str' === input.type"
                            outlined
                            dense
                        />
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
                <v-btn :disabled="availableArguments.length === 0"
                       @click="() => suiteInputs.push({name: availableArguments[0], type: typesByName[availableArguments[0]][0], value: ''})">
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

import {computed, onMounted, ref} from 'vue';
import mixpanel from 'mixpanel-browser';
import {api} from '@/api';
import {GenerateTestSuiteDTO, GenerateTestSuiteInputDTO, TestCatalogDTO} from '@/generated-sources';
import {useRouter} from 'vue-router/composables';
import {chain} from 'lodash';
import DatasetSelector from '@/views/main/utils/DatasetSelector.vue';
import ModelSelector from '@/views/main/utils/ModelSelector.vue';

const {projectKey, projectId} = defineProps<{
  projectKey: string,
  projectId: number
}>();

let registry = ref<TestCatalogDTO | null>(null);
const dialog = ref<boolean>(false);
const name = ref<string>('');
const suiteInputs = ref<GenerateTestSuiteInputDTO[]>([]);

const router = useRouter();


onMounted(async () => {
  registry.value = await api.getTestsCatalog(projectId);
});

async function submit(close) {
  mixpanel.track('Create test suite v2', {
    projectKey
  });

  const createdTestSuiteId = await api.generateTestSuite(projectKey, {
    name: name.value,
    inputs: suiteInputs.value
  } as GenerateTestSuiteDTO);

  dialog.value = false;
  await router.push({name: 'test-suite-new', params: {suiteId: createdTestSuiteId.toString()}});

  close();
}

const typesByName = computed(() => registry.value === null ? {} :
    chain(registry.value.tests)
        .values()
        .flatMap(definition => Object.values(definition.arguments))
        .filter(argument => !argument.optional)
        .groupBy('name')
        .mapValues(args => chain(args)
            .map('type')
            .uniq()
            .value())
        .value()
)

const argumentNames = computed(() => Object.keys(typesByName.value));
const availableArguments = computed(() => argumentNames.value
    .filter(name => suiteInputs.value.find(input => input.name === name) === undefined))
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

</style>
