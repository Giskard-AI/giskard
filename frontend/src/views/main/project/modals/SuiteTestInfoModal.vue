<template>
  <vue-final-modal
      v-slot="{ close }"
      v-bind="$attrs"
      classes="modal-container"
      content-class="modal-content"
      v-on="$listeners"
  >
    <div class="text-center">
      <v-card>
        <v-card-title>
          {{ test.displayName ?? test.name }}
        </v-card-title>
        <v-card-text class="card-content">
          <pre class="test-doc caption pt-5">{{ test.doc }}</pre>
          <p class="text-h6 pt-4">Inputs</p>
          <v-list-item v-for="a in sortedArguments" :key="a.name" class="pl-0 pr-0">
            <v-row>
              <v-col>
                <v-list-item-content style="border: 1px solid">
                  <v-list-item-title>{{ a && a.name }}</v-list-item-title>
                  <v-list-item-avatar>
                  <span v-if="suiteTest.testInputs[a.name]?.isAlias">
                    {{ suiteTest.testInputs[a.name].value }}
                  </span>
                    <span v-else-if="a.name in suiteTest.testInputs && a.type === 'Model'">
                    {{
                        models[suiteTest.testInputs[a.name].value].name ?? models[suiteTest.testInputs[a.name].value].id
                      }}
                  </span>
                    <span v-else-if="a.name in suiteTest.testInputs && a.type === 'Dataset'">
                    {{
                        datasets[suiteTest.testInputs[a.name].value].name ?? datasets[suiteTest.testInputs[a.name].value].id
                      }}
                  </span>
                    <span v-else-if="a && a.name in suiteTest.testInputs">{{
                        suiteTest.testInputs[a.name].value
                      }}</span>
                  </v-list-item-avatar>
                  <v-list-item-subtitle class="text-caption">{{ a.type }}</v-list-item-subtitle>
                  <v-list-item-action-text v-show="!!a.optional">Optional. Default: <code>{{ a.defaultValue }}</code>
                  </v-list-item-action-text>
                </v-list-item-content>
              </v-col>
            </v-row>
          </v-list-item>
          <v-row>
            <v-col>
              <v-expansion-panels flat @change="resizeEditor">
                <v-expansion-panel>
                  <v-expansion-panel-header class="pa-0">Code</v-expansion-panel-header>
                  <v-expansion-panel-content class="pa-0">
                    <MonacoEditor
                        ref="editor"
                        v-model='test.code'
                        class='editor'
                        language='python'
                        style="height: 300px; min-height: 300px"
                        :options="monacoOptions"
                    />
                  </v-expansion-panel-content>
                </v-expansion-panel>
              </v-expansion-panels>
            </v-col>
          </v-row>
        </v-card-text>
        <v-card-actions>

        </v-card-actions>
      </v-card>
    </div>
  </vue-final-modal>
</template>

<script setup lang="ts">

import {SuiteTestDTO, TestFunctionDTO} from '@/generated-sources';
import {computed, ref} from 'vue';
import _ from 'lodash';
import {storeToRefs} from 'pinia';
import {useTestSuiteStore} from '@/stores/test-suite';
import MonacoEditor from 'vue-monaco';

const l = MonacoEditor;

const {suiteTest, test} = defineProps<{
  suiteTest: SuiteTestDTO,
  test: TestFunctionDTO
}>();

const {models, datasets} = storeToRefs(useTestSuiteStore());

const editor = ref(null)

const sortedArguments = computed(() => {
  if (!test) {
    return [];
  }

  return _.sortBy(_.values(test.args), value => {
    return !_.isUndefined(suiteTest.testInputs[value.name]);
  }, 'name');
})

function resizeEditor() {
  setTimeout(() => {
    editor.value.editor.layout();
  })
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

.card-content {
  text-align: start;
}

</style>
