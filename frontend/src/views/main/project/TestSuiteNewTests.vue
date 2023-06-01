<template>
  <v-row v-if="suite">
    <v-col cols="3">
      <v-list three-line v-if="suite.tests">
        <v-list-item-group v-model="selectedTest" color="primary" mandatory>
          <template v-for="(test) in suite.tests">
            <v-divider/>
            <v-list-item :value="test">
              <v-list-item-content>
                <v-list-item-title v-text="registryByTestUuid[test.testUuid].name"
                                   class="test-title"></v-list-item-title>
              </v-list-item-content>
            </v-list-item>
          </template>
        </v-list-item-group>
      </v-list>
    </v-col>
    <v-col v-if="selectedTest">
      <v-row>
        <v-col>
          <TestSuiteTestDetails
              :test="registryByTestUuid[selectedTest.testUuid]"
              :inputs="selectedTest.testInputs"
              :executions="testSuiteResults[selectedTest.testUuid]"/>
        </v-col>
      </v-row>
    </v-col>
  </v-row>
</template>

<script lang="ts" setup>

import {useTestSuiteStore} from '@/stores/test-suite';
import {computed, ref, watch} from 'vue';
import {SuiteTestDTO} from '@/generated-sources';
import TestSuiteTestDetails from '@/views/main/project/TestSuiteTestDetails.vue';
import {storeToRefs} from 'pinia';
import {chain} from 'lodash';


const {registry, suite, testSuiteResults} = storeToRefs(useTestSuiteStore());

const selectedTest = ref<SuiteTestDTO | null>(null);

watch(() => suite.value, () => {
  if (selectedTest.value !== null && suite.value !== null) {
    selectedTest.value = suite.value.tests.find(test => test.testUuid === selectedTest.value!.testUuid) ?? null;
  }
})

const registryByTestUuid = computed(() => chain(registry.value).keyBy('uuid').value())

</script>
