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
                <ValidationProvider name="Test suite name" rules="required" v-slot="{errors}">
                  <v-text-field label="Test suite name" autofocus v-model="name" :error-messages="errors" outlined></v-text-field>
                </ValidationProvider>
                <v-switch v-model="shouldCreateAutoTests" :label="'Create tests automatically'" disabled></v-switch>
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

import {ref} from 'vue';
import mixpanel from 'mixpanel-browser';
import {api} from '@/api';
import {TestSuiteNewDTO} from '@/generated-sources';
import {useRouter} from 'vue-router/composables';

const { projectKey } = defineProps<{
  projectKey: string
}>();

const dialog = ref<boolean>(false);
const name = ref<string>('');
const shouldCreateAutoTests = ref<boolean>(false);

const router = useRouter();

async function submit(close) {
  mixpanel.track('Create test suite v2', {
    projectKey,
    shouldGenerateTests: shouldCreateAutoTests.value
  });

  const createdTestSuiteId = await api.createTestSuitesNew(projectKey, {
    id: null,
    name: name.value,
    tests: [],
    projectKey: projectKey
  } as TestSuiteNewDTO, shouldCreateAutoTests.value);

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
}

</style>
