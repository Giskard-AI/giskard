<template>
  <v-list>
    <v-list-item v-for="(input, index) in inputs" :track-by="input" class="pl-0 pr-0">
      <v-row>
        <v-col>
          <v-list-item-content class="py-2">
            <v-list-item-title class="input-name">{{ input.name }}: <span class="input-type">{{ input.type }}</span>
              <span v-if="test?.args[index].optional" class="input-type">= {{
                  test.args[index].defaultValue ?? 'None'
                }}</span>
              <v-tooltip v-if="doc && doc.args.hasOwnProperty(input.name)" bottom>
                <template v-slot:activator="{ on, attrs }">
                  <v-icon v-bind="attrs" v-on="on">info</v-icon>
                </template>
                <span>{{ doc.args[input.name] }}</span>
              </v-tooltip>
            </v-list-item-title>
          </v-list-item-content>
        </v-col>
        <v-col class="input-column">
          <template v-if="!editing">
            <span v-if="!props.functionInputs"/>
            <span v-else-if="props.functionInputs[input.name]?.isAlias">
                            {{ props.functionInputs[input.name].value }}
                        </span>
            <span v-else-if="input.name in props.functionInputs && input.type === 'BaseModel'">
                            {{
                models[props.functionInputs[input.name].value].name ?? models[props.functionInputs[input.name].value].id
              }}
                        </span>
            <span v-else-if="input.name in props.functionInputs && input.type === 'Dataset'">
                            {{
                datasets[props.functionInputs[input.name].value].name ?? datasets[props.functionInputs[input.name].value].id
              }}
                        </span>
            <span v-else-if="input.name in props.functionInputs && input.type === 'SlicingFunction'">
                            {{
                slicingFunctionsByUuid[props.functionInputs[input.name].value].displayName
                ?? slicingFunctionsByUuid[props.functionInputs[input.name].value].name
              }}
                        </span>
            <span v-else-if="input && input.name in props.functionInputs">{{
                props.functionInputs[input.name].value
              }}
                        </span>
          </template>
          <template v-else-if="props.modelValue">
            <DatasetSelector v-if="input.type === 'Dataset'" :label="input.name" :project-id="projectId"
                             :return-object="false" :value.sync="props.modelValue[input.name].value"
                             :disabled="readOnlyInputs.includes(input.name)"/>
            <ModelSelector v-else-if="input.type === 'BaseModel'" :label="input.name" :project-id="projectId"
                           :return-object="false" :value.sync="props.modelValue[input.name].value"
                           :disabled="readOnlyInputs.includes(input.name)"/>
            <SlicingFunctionSelector v-else-if="input.type === 'SlicingFunction'"
                                     :args.sync="props.modelValue[input.name].params"
                                     :label="input.name"
                                     :project-id="projectId"
                                     :value.sync="props.modelValue[input.name].value"
                                     :disabled="readOnlyInputs.includes(input.name)"/>
            <TransformationFunctionSelector v-else-if="input.type === 'TransformationFunction'"
                                            :args.sync="props.modelValue[input.name].params"
                                            :label="input.name"
                                            :project-id="projectId"
                                            :value.sync="props.modelValue[input.name].value"
                                            :disabled="readOnlyInputs.includes(input.name)"/>
            <KwargsCodeEditor v-else-if="input.type === 'Kwargs'" :value.sync="props.modelValue[input.name].value"/>
            <v-text-field v-else-if="['float', 'int'].includes(input.type)" v-model="props.modelValue[input.name].value"
                          :label="input.name" :step='input.type === "float" ? 0.1 : 1' dense hide-details outlined
                          type="number" :disabled="readOnlyInputs.includes(input.name)"></v-text-field>
            <v-textarea v-else-if="input.type === 'str'" v-model="props.modelValue[input.name].value"
                        :label="input.name" dense hide-details outlined type="text" rows="1"
                        :disabled="readOnlyInputs.includes(input.name)" auto-grow></v-textarea>
            <v-switch v-else-if="input.type === 'bool'" v-model="props.modelValue[input.name].value"
                      :label="props.modelValue[input.name].value ? 'True' : 'False'" dense :disabled="readOnlyInputs.includes(input.name)"></v-switch>
          </template>
        </v-col>
      </v-row>
    </v-list-item>
  </v-list>
</template>

<script lang="ts" setup>
import DatasetSelector from '@/views/main/utils/DatasetSelector.vue';
import ModelSelector from '@/views/main/utils/ModelSelector.vue';
import {computed} from 'vue';
import {FunctionInputDTO, TestFunctionDTO} from '@/generated-sources';
import {storeToRefs} from 'pinia';
import {useTestSuiteStore} from '@/stores/test-suite';
import SlicingFunctionSelector from "@/views/main/utils/SlicingFunctionSelector.vue";
import {useCatalogStore} from "@/stores/catalog";
import TransformationFunctionSelector from "@/views/main/utils/TransformationFunctionSelector.vue";
import KwargsCodeEditor from "@/views/main/utils/KwargsCodeEditor.vue";
import {ParsedDocstring} from "@/utils/python-doc.utils";

interface Props {
  functionInputs?: { [key: string]: FunctionInputDTO };
  test?: TestFunctionDTO;
  projectId: number;
  inputs: { [name: string]: string };
  modelValue?: { [name: string]: FunctionInputDTO };
  editing: boolean;
  doc?: ParsedDocstring;
  readOnlyInputs?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  readOnlyInputs: () => []
})

const {models, datasets} = storeToRefs(useTestSuiteStore());
const {slicingFunctionsByUuid} = storeToRefs(useCatalogStore());

const inputs = computed(() => Object.keys(props.inputs).map((name) => ({
  name,
  type: props.inputs[name]
})));
</script>

<style lang="scss" scoped>
.input-column {
  width: 300px;
}

.input-name {
  font-family: 'Roboto Mono', monospace;
  opacity: 0.875;
  white-space: break-spaces;
}

.input-type {
  font-size: 0.875rem;
  opacity: 0.875;
}
</style>
