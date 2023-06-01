<template>
  <v-row v-if="registry">
    <v-col cols="3">
      <v-list three-line v-if="suite.tests">
        <v-list-item-group v-model="selectedTest" color="primary" mandatory>
          <template v-for="(test) in suite.tests">
            <v-divider/>
            <v-list-item :value="test">
              <v-list-item-content>
                <v-list-item-title v-text="registry.tests[test.testId].name"
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
              :test="registry.tests[selectedTest.testId]"
              :inputs="selectedTest.testInputs"
              :executions="testSuiteResults[selectedTest.testId]"/>
        </v-col>
      </v-row>
    </v-col>
  </v-row>
</template>

<script lang="ts" setup>

import {useTestSuiteStore} from '@/stores/test-suite';
import {ref} from 'vue';
import {SuiteTestDTO} from '@/generated-sources';
import TestSuiteTestDetails from '@/views/main/project/TestSuiteTestDetails.vue';
import {storeToRefs} from 'pinia';


const {testSuiteResults} = useTestSuiteStore();
const {registry, suite} = storeToRefs(useTestSuiteStore());

const selectedTest = ref<SuiteTestDTO | null>(null);

</script>
