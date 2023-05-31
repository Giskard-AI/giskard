<template>
  <vue-final-modal
      v-slot="{ close }"
      v-bind="$attrs"
      classes="modal-container"
      content-class="modal-content"
      v-on="$listeners"
  >
    <div class="text-center">
        <v-card class="modal-card">
            <v-card-title>
                {{ suiteTest.test.displayName ?? suiteTest.test.name }}
            </v-card-title>
            <v-card-text class="card-content">
                <pre class="test-doc caption pt-5">{{ doc.body }}</pre>
                <div class="d-flex align-center">
                    <p class="text-h6 pt-4">Inputs</p>
                </div>
                <TestInputListSelector v-if="suiteTest.test.args"
                                       :test-inputs="suiteTest.functionInputs"
                                       :test="testFunctionsByUuid[suiteTest.testUuid]"
                                       :model-value="editedInputs"
                                       :project-id="projectId"
                                       :inputs="inputType"
                                       :doc="doc"
                                       @invalid="i => invalid = i"
                                       @result="v => result = v"
              />
              <v-row>
                  <v-col>
                      <v-expansion-panels flat @change="resizeEditor">
                          <v-expansion-panel>
                              <v-expansion-panel-header class="pa-0">Code</v-expansion-panel-header>
                              <v-expansion-panel-content class="pa-0">
                                  <MonacoEditor
                                          ref="editor"
                                          v-model='suiteTest.test.code'
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
              <v-spacer/>
              <v-btn color="green" @click="close" disabled>
                  <v-icon>mdi-bug</v-icon>
                  Debug
              </v-btn>
              <v-btn color="primary" @click="() => saveEditedInputs(close)" :disabled="invalid">
                  <v-icon>save</v-icon>
                  Save
              </v-btn>
          </v-card-actions>
      </v-card>
    </div>
  </vue-final-modal>
</template>

<script setup lang="ts">

import {FunctionInputDTO, SuiteTestDTO} from '@/generated-sources';
import {computed, inject, onMounted, ref} from 'vue';
import _, {chain} from 'lodash';
import {storeToRefs} from 'pinia';
import {useTestSuiteStore} from '@/stores/test-suite';
import MonacoEditor from 'vue-monaco';
import {api} from '@/api';
import {editor} from 'monaco-editor';
import TestInputListSelector from "@/components/TestInputListSelector.vue";
import {useCatalogStore} from "@/stores/catalog";
import {extractArgumentDocumentation} from "@/utils/python-doc.utils";
import IEditorOptions = editor.IEditorOptions;

const l = MonacoEditor;
const monacoOptions: IEditorOptions = inject('monacoOptions');
monacoOptions.readOnly = true;

const props = defineProps<{
    suiteTest: SuiteTestDTO
}>();

const {models, datasets, projectId, suite, inputs} = storeToRefs(useTestSuiteStore());
const {reload} = useTestSuiteStore();

const editedInputs = ref<{ [input: string]: FunctionInputDTO }>({});
const result = ref<{ [input: string]: FunctionInputDTO }>({});
const editor = ref(null)

const {testFunctionsByUuid} = storeToRefs(useCatalogStore())

const sortedArguments = computed(() => {
    return _.sortBy(_.values(props.suiteTest.test.args), value => {
        return !_.isUndefined(props.suiteTest.functionInputs[value.name]);
    }, 'name');
})

const doc = computed(() => extractArgumentDocumentation(props.suiteTest.test))


const invalid = ref(false);

function resizeEditor() {
    setTimeout(() => {
        editor.value.editor.layout();
    })
}

onMounted(() => {
    editedInputs.value = Object.values(props.suiteTest.functionInputs)
        .reduce((e, arg) => {
            e[arg.name] = {
                ...arg
            };
            return e;
        }, {});

});

async function saveEditedInputs(close) {
    await api.updateTestInputs(projectId.value!, suite.value!.id!, props.suiteTest.id!, Object.values(result.value))

    await reload();
    close();
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
}

.modal-card {
    max-height: 80vh;
    min-width: 72rem;
    display: flex;
    flex-direction: column;
}

.card-content {
    text-align: start;
    flex-grow: 1;
    overflow: auto;
}

</style>
