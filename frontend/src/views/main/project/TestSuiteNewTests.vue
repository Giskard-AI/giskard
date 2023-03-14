<template>
  <div class="vc">
    <v-container class="main-container vc">
      <v-row v-if="registry" class="fill-height">
        <v-col cols="3" class="vc fill-height">
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
        <v-col v-if="selectedTest" class="vc fill-height">
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
    </v-container>
  </div>
</template>

<script lang="ts" setup>

import {useTestSuiteStore} from '@/stores/test-suite';
import {ref, watch} from 'vue';
import {SuiteTestDTO} from '@/generated-sources';
import TestSuiteTestDetails from '@/views/main/project/TestSuiteTestDetails.vue';
import {storeToRefs} from 'pinia';


const {registry, suite, testSuiteResults} = storeToRefs(useTestSuiteStore());

const selectedTest = ref<SuiteTestDTO | null>(null);

watch(() => suite.value, () => {
  if (selectedTest.value !== null && suite.value !== null) {
    selectedTest.value = suite.value.tests.find(test => test.testId === selectedTest.value!.testId) ?? null;
  }
})

</script>

<style scoped lang="scss">
.main-container {
  width: 100%;
  max-width: 100%;
}
</style>
