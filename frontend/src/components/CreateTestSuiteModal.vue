<template>
  <v-dialog
      v-model="dialog"
      width="500"
  >
    <template v-slot:activator="{ on, attrs }">
      <v-btn
          color="primary"
          v-bind="attrs"
          v-on="on"
      >
        New test suite
      </v-btn>
    </template>

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
                @click="submit"
                :disabled="invalid"
            >
              Create
            </v-btn>
          </v-card-actions>
        </v-card>
      </ValidationObserver>
    </v-form>
  </v-dialog>
</template>

<script setup lang="ts">

import {onMounted, ref} from 'vue';
import mixpanel from 'mixpanel-browser';
import {api} from '@/api';
import {ProjectDTO, TestSuiteNewDTO} from '@/generated-sources';
import {useRouter} from 'vue-router/composables';

const { projectId } = defineProps<{
  projectId: number
}>();

const dialog = ref<boolean>(false);
const name = ref<string>('');
const shouldCreateAutoTests = ref<boolean>(false);
const project = ref<ProjectDTO | null>(null);

onMounted(async () => project.value = await api.getProject(projectId));

const router = useRouter();

async function submit() {
  if (project.value === null) {
    return;
  }

  mixpanel.track('Create test suite v2', {
    projectId,
    shouldGenerateTests: shouldCreateAutoTests.value
  });

  const createdTestSuiteId = await api.createTestSuitesNew(project.value.key, {
    id: null,
    name: name.value,
    tests: [],
    projectKey: project.value.key
  } as TestSuiteNewDTO, shouldCreateAutoTests.value);

  dialog.value = false;
  await router.push({name: 'test-suite-new', params: {suiteId: createdTestSuiteId.toString()}});
}
</script>
