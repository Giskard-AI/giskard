<template>
    <vue-final-modal v-slot="{ close }" v-bind="$attrs" classes="modal-container" content-class="modal-content" v-on="$listeners">
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
                    <TestInputListSelector v-if="suiteTest.test.args" :test-inputs="suiteTest.functionInputs" :test="testFunctionsByUuid[suiteTest.testUuid]" :model-value="editedInputs" :project-id="projectId" :inputs="inputType" :doc="doc" @invalid="i => invalid = i" @result="v => result = v" />
                    <v-row>
                        <v-col>
                            <v-expansion-panels flat @change="resizeEditor">
                                <v-expansion-panel>
                                    <v-expansion-panel-header class="pa-0">Code</v-expansion-panel-header>
                                    <v-expansion-panel-content class="pa-0">
                                        <CodeSnippet :codeContent="suiteTest.test.code" :language="'python'"></CodeSnippet>
                                    </v-expansion-panel-content>
                                </v-expansion-panel>
                            </v-expansion-panels>
                        </v-col>
                    </v-row>
                </v-card-text>
                <v-card-actions>
                    <v-spacer />
                    <v-btn color="error" text @click="() => removeTest(close)" class="pr-2">
                        <v-icon>delete</v-icon>
                        Remove test
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
import {computed, onMounted, ref} from 'vue';
import _, {chain} from 'lodash';
import {storeToRefs} from 'pinia';
import {useTestSuiteStore} from '@/stores/test-suite';
import {api} from '@/api';
import TestInputListSelector from "@/components/TestInputListSelector.vue";
import {useCatalogStore} from "@/stores/catalog";
import {$vfm} from "vue-final-modal";
import RunTestModal from "@/views/main/project/modals/RunTestModal.vue";
import {extractArgumentDocumentation} from "@/utils/python-doc.utils";
import {$vfm} from "vue-final-modal";
import ConfirmModal from "@/views/main/project/modals/ConfirmModal.vue";
import CodeSnippet from '@/components/CodeSnippet.vue';
import mixpanel from "mixpanel-browser";
import {anonymize} from "@/utils";

const props = defineProps<{
  suiteTest: SuiteTestDTO
}>();

const {projectId, suite} = storeToRefs(useTestSuiteStore());
const {reload} = useTestSuiteStore();

const editedInputs = ref<{ [input: string]: FunctionInputDTO }>({});
const result = ref<{ [input: string]: FunctionInputDTO }>({});

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

    mixpanel.track('Edit test inputs of test suite', {
        suiteId: suite.value!.id,
        projectKey: suite.value!.projectKey,
        testUuid: props.suiteTest.testUuid,
        testName: props.suiteTest.test.displayName ?? props.suiteTest.test.name,
        inputs: Object.values(result.value).map(({value, ...data}) => ({
            ...data,
            value: anonymize(value)
        }))
    });
}

const inputType = computed(() => chain(sortedArguments.value)
    .keyBy('name')
    .mapValues('type')
    .value()
);

async function runDebug() {
  await $vfm.show({
    component: RunTestModal,
    bind: {
      projectId: projectId.value,
      suiteId: suite.value!.id,
      inputs: inputs.value,
      testUuid: props.suiteTest.testUuid,
      compareMode: false,
      previousParams: {},
      debug: true
    }
  });
}

async function removeTest(close) {
    await $vfm.show({
        component: ConfirmModal,
        bind: {
            title: 'Remove test',
            text: `Are you sure that you want to remove this test from the test suite?`,
            isWarning: true
        },
        on: {
            async confirm(closeConfirm) {
                await api.removeTest(suite.value!.projectKey!, suite.value!.id!, props.suiteTest.id!);
                await useTestSuiteStore().reload();
                closeConfirm();
                close();

                mixpanel.track('Removed test form test suite', {
                    suiteId: suite.value!.id,
                    projectKey: suite.value!.projectKey,
                    testUuid: props.suiteTest.testUuid,
                    testName: props.suiteTest.test.displayName ?? props.suiteTest.test.name
                });
            }
        }
    });
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

.modal-card {
  max-height: 80vh;
  min-width: 72rem;display: flex;
  flex-direction: column;
}

.card-content {
  text-align: start;
  flex-grow: 1;
  overflow: auto;
}
</style>
