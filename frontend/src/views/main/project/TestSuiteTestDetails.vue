<template>
  <div>
    <div class="text-h5">{{ props.test.name }}</div>
    <pre class="text-caption">{{ props.test.doc }}</pre>

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
    <div>
      <v-list v-if="props.test.arguments && editedInputs === null">
        <v-list-item v-for="a in sortedArguments" :key="a.name" class="pl-0 pr-0">
          <v-row>
            <v-col>
              <v-list-item-content style="border: 1px solid">
                <v-list-item-title>{{ a && a.name }}</v-list-item-title>
                <v-list-item-avatar>
                  <span v-if="props.inputs[a.name]?.isAlias">
                    {{ props.inputs[a.name].value }}
                  </span>
                  <span v-else-if="a.name in props.inputs && a.type === 'Dataset'">
                    {{ props.datasets[props.inputs[a.name].value] }}
                  </span>
                  <span v-else-if="a && a.name in props.inputs">{{ props.inputs[a.name].value }}</span>
                </v-list-item-avatar>
                <v-list-item-subtitle class="text-caption">{{ a.type }}</v-list-item-subtitle>
                <v-list-item-action-text v-show="!!a.optional">Optional. Default: <code>{{ a.defaultValue }}</code>
                </v-list-item-action-text>
              </v-list-item-content>
            </v-col>
          </v-row>
        </v-list-item>
      </v-list>
      <TestInputListSelector v-else-if="props.test.arguments"
                             :model-value="editedInputs"
                             :project-id="props.projectId"
                             :inputs="inputType"/>
    </div>

    <div v-if="props.executions?.length > 0">
      <div class="d-flex justify-space-between align-center">
        <p class="text-h6">Results</p>
        <v-btn text color="secondary" :to="{name: 'test-suite-new-compare-test', params: { testId: props.test.id}}">
          Compare executions
          <v-icon>compare</v-icon>
        </v-btn>
      </div>
      <TestResultTimeline :executions="props.executions"/>
    </div>

  </div>
</template>

<script lang="ts" setup>

import {DatasetDTO, ModelDTO, SuiteTestExecutionDTO, TestDefinitionDTO, TestInputDTO} from "@/generated-sources";
import _, {chain} from "lodash";
import TestResultTimeline from '@/components/TestResultTimeline.vue';
import {computed, ref, watch} from 'vue';
import TestInputListSelector from '@/components/TestInputListSelector.vue';
import {api} from '@/api';

const props = defineProps<{
  projectId: number,
  suiteId: number,
  test: TestDefinitionDTO
  inputs: { [key: string]: TestInputDTO },
  models: { [key: string]: ModelDTO },
  datasets: { [key: string]: DatasetDTO },
  executions?: SuiteTestExecutionDTO[]
}>();

const editedInputs = ref<{ [input: string]: string} | null>(null);

const emit = defineEmits(['updateTestSuite']);

const sortedArguments = computed(() => {
  if (!props.test) {
    return [];
  }

  return _.sortBy(_.values(props.test.arguments), value => {
    return !_.isUndefined(props.inputs[value.name]);
  }, 'name');
})

function editInputs() {
  editedInputs.value = Object.keys(props.test.arguments)
      .reduce((editedInputs, arg) => {
        editedInputs[arg] = props.inputs[arg]?.value;
        return editedInputs;
      }, {});
}

async function saveEditedInputs() {
  if (editedInputs.value === null) {
    return;
  }

  const saved = await api.updateTestInputs(props.projectId, props.suiteId, props.test.id, editedInputs.value)
  editedInputs.value = null;

  emit('updateTestSuite', saved);
}

watch(() => props.test, () => editedInputs.value = null);

const inputType = computed(() => chain(sortedArguments.value)
    .keyBy('name')
    .mapValues('type')
    .value()
);
</script>
