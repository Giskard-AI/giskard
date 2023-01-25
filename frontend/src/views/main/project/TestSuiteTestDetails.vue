<template>
  <div>
    <div class="text-h5">{{ props.test.name }}</div>
    <pre class="text-caption">{{ props.test.doc }}</pre>

    <p class="text-h6">Inputs</p>
    <div>
      <v-list v-if="props.test.arguments">
        <v-list-item v-for="a in sortedArguments(props.test.arguments)" class="pl-0 pr-0">
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

import {
  DatasetDTO,
  ModelDTO,
  SuiteTestExecutionDTO,
  TestDefinitionDTO,
  TestFunctionArgumentDTO,
  TestInputDTO
} from "@/generated-sources";
import _ from "lodash";
import TestResultTimeline from '@/components/TestResultTimeline.vue';

const props = defineProps<{
  projectId: number,
  test: TestDefinitionDTO
  inputs: { [key: string]: TestInputDTO },
  models: { [key: string]: ModelDTO },
  datasets: { [key: string]: DatasetDTO },
  executions: SuiteTestExecutionDTO[]
}>();

function sortedArguments(args: { [key: string]: TestFunctionArgumentDTO }) {
  return _.sortBy(_.values(args), value => {
    return !_.isUndefined(props.inputs[value.name]);
  }, 'name');
}
</script>
