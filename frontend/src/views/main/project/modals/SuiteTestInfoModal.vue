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
          <div class="d-flex align-center">
            <p class="text-h6 pt-4">Inputs</p>
            <v-btn v-if="editedInputs === null" icon @click="editInputs()" color="primary">
              <v-icon right>edit</v-icon>
            </v-btn>
            <div v-else>
              <v-btn icon @click="saveEditedInputs()" color="primary">
                <v-icon right>save</v-icon>
              </v-btn>
              <v-btn icon @click="editedInputs = null" color="error">
                <v-icon right>cancel</v-icon>
              </v-btn>
            </div>
          </div>
          <TestInputListSelector v-if="test.args"
                                 :test-inputs="suiteTest.testInputs"
                                 :test="registryByUuid[suiteTest.testUuid]"
                                 :model-value="editedInputs"
                                 :project-id="projectId"
                                 :inputs="inputType"
                                 :shared-inputs="suite.testInputs"
                                 :editing="editedInputs !== null"/>
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

import {SuiteTestDTO, TestFunctionDTO, TestInputDTO} from '@/generated-sources';
import {computed, inject, ref} from 'vue';
import _, {chain} from 'lodash';
import {storeToRefs} from 'pinia';
import {useTestSuiteStore} from '@/stores/test-suite';
import MonacoEditor from 'vue-monaco';
import {api} from '@/api';
import TestInputListSelector from '@/components/TestInputListSelector.vue';
import {editor} from 'monaco-editor';
import IEditorOptions = editor.IEditorOptions;

const l = MonacoEditor;
const monacoOptions: IEditorOptions = inject('monacoOptions');
monacoOptions.readOnly = true;

const {suiteTest, test} = defineProps<{
  suiteTest: SuiteTestDTO,
  test: TestFunctionDTO
}>();

const {models, datasets, projectId, suite, inputs, registry} = storeToRefs(useTestSuiteStore());
const {reload} = useTestSuiteStore();

const editedInputs = ref<{ [input: string]: TestInputDTO } | null>(null);
const editor = ref(null)

const sortedArguments = computed(() => {
  if (!test) {
    return [];
  }

  return _.sortBy(_.values(test.args), value => {
    return !_.isUndefined(suiteTest.testInputs[value.name]);
  }, 'name');
})

const registryByUuid = computed(() => chain(registry.value).keyBy('uuid').value());

function resizeEditor() {
  setTimeout(() => {
    editor.value.editor.layout();
  })
}

function editInputs() {
  editedInputs.value = test.args
      .reduce((editedInputs, arg) => {
        editedInputs[arg.name] = {
          ...suiteTest.testInputs[arg.name],
          name: arg.name
        };
        return editedInputs;
      }, {});
}

async function saveEditedInputs() {
  if (editedInputs.value === null) {
    return;
  }

  await api.updateTestInputs(projectId.value!, suite.value!.id!, test.uuid, Object.values(editedInputs.value))
  editedInputs.value = null;

  await reload();
}

const inputType = computed(() => chain(sortedArguments.value)
    .keyBy('name')
    .mapValues('type')
    .value()
);
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
  max-height: 80vh;
  overflow: auto;

}

.card-content {
  text-align: start;
}

</style>
