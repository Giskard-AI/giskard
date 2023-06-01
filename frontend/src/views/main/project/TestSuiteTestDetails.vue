<template>
  <div>
    <div class="text-h5">{{ props.test.name }}</div>
    <pre class="text-caption">{{ props.test.doc }}</pre>

    <div>Inputs</div>
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
                    {{ allDatasets[props.inputs[a.name].value] }}
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

  </div>
</template>

<script lang="ts" setup>

import {DatasetDTO, ModelDTO, TestDefinitionDTO, TestFunctionArgumentDTO, TestInputDTO} from "@/generated-sources";
import {api} from "@/api";
import {onMounted, ref} from "vue";
import _ from "lodash";

const props = defineProps<{
  projectId: number,
  test: TestDefinitionDTO
  inputs: { [key: string]: TestInputDTO }
}>();
let allDatasets = ref<{ [key: string]: DatasetDTO }>({});
let allModels = ref<{ [key: string]: ModelDTO }>({});
onMounted(async () => {
  const datasets = await api.getProjectDatasets(props.projectId);
  allDatasets.value = Object.fromEntries(datasets.map(x => [x.id, x]));


  const models = await api.getProjectModels(props.projectId);
  allModels.value = Object.fromEntries(models.map(x => [x.id, x]));
});

function sortedArguments(args: { [key: string]: TestFunctionArgumentDTO }) {
  return _.sortBy(_.values(args), value => {
    return !_.isUndefined(props.inputs[value.name]);
  }, 'name');
}
</script>