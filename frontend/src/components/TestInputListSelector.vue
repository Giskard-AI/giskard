<template>
  <v-list>
    <v-list-item v-for="input in inputs" :track-by="input" class="pl-0 pr-0">
      <v-row>
        <v-col cols="3">
          <v-list-item-content>
            <v-list-item-title>
              {{ input.name }}
              <v-tooltip v-if="doc && doc.args.hasOwnProperty(input.name)" bottom>
                <template v-slot:activator="{ on, attrs }">
                  <v-icon v-bind="attrs" v-on="on">info</v-icon>
                </template>
                <span>{{ doc.args[input.name] }}</span>
              </v-tooltip>
            </v-list-item-title>
            <v-list-item-subtitle class="text-caption">{{ input.type }}</v-list-item-subtitle>
            <v-list-item-action-text v-if="props.test && !!props.test.args.find(a => a.name === input.name).optional">
              Optional. Default:
              <code>{{ props.test.args.find(a => a.name === input.name).defaultValue }}</code>
            </v-list-item-action-text>
          </v-list-item-content>
        </v-col>
        <v-col cols="3">
          <v-select v-model="buttonToggleValues[input.name]" :items="inputTypeSelector" dense hide-details
                    item-text="name"
                    outlined return-object @change="item => item.select(input.name)">
            <template v-slot:item="data">
              <div class="pt-2 pb-2">
                <span>{{ data.item.name }}</span><br/>
                <span class="text-caption">{{ data.item.description }}</span>
              </div>
            </template>
          </v-select>
        </v-col>
        <v-col :cols="6">
          <div v-if="editedInputs" class="d-flex">
            <ValidationProvider v-if="!editedInputs.hasOwnProperty(input.name) || editedInputs[input.name].isAlias"
                                v-slot="{ errors }" mode="eager" name="alias" rules="required" class="flex-1">
              <v-select v-model="editedInputs[input.name].value" :error-messages="errors"
                        :items="aliases[input.type] ?? []" :menu-props="{
                                closeOnClick: true,
                                closeOnContentClick: true,
                            }"
                        clearable dense outlined>
                <template v-slot:prepend-item>
                  <v-list-item ripple @click="() => createAlias(input.name, input.type)" @mousedown.prevent>
                    <v-list-item-action>
                      <v-icon>
                        add
                      </v-icon>
                    </v-list-item-action>
                    <v-list-item-content>
                      <v-list-item-title>
                        Create new alias
                      </v-list-item-title>
                    </v-list-item-content>
                  </v-list-item>
                  <v-divider class="mt-2"></v-divider>
                </template>
              </v-select>
            </ValidationProvider>
            <template v-else="!editedInputs[input.name].isAlias">
              <DatasetSelector v-if="input.type === 'Dataset'" :label="input.name" :project-id="projectId"
                               :return-object="false" :value.sync="editedInputs[input.name].value"/>
              <ModelSelector v-else-if="input.type === 'BaseModel'" :label="input.name" :project-id="projectId"
                             :return-object="false" :value.sync="editedInputs[input.name].value"/>
              <SlicingFunctionSelector v-else-if="input.type === 'SlicingFunction'"
                                       :args.sync="editedInputs[input.name].params"
                                       :label="input.name" :project-id="projectId"
                                       :value.sync="editedInputs[input.name].value"/>
              <TransformationFunctionSelector v-else-if="input.type === 'TransformationFunction'"
                                              :args.sync="editedInputs[input.name].params" :label="input.name"
                                              :project-id="projectId"
                                              :value.sync="editedInputs[input.name].value"/>
              <KwargsCodeEditor v-else-if="input.type === 'Kwargs'" :value.sync="editedInputs[input.name].value"/>
              <ValidationProvider v-else-if="['float', 'int'].includes(input.type)" v-slot="{ errors }" mode="eager"
                                  name="value" rules="required" class="flex-1">
                <v-text-field v-model="editedInputs[input.name].value" :error-messages="errors"
                              :step='input.type === "float" ? 0.1 : 1' dense outlined single-line type="number"/>
              </ValidationProvider>
              <ValidationProvider v-else-if="input.type === 'str'" v-slot="{ errors }" mode="eager" name="input"
                                  rules="required" class="flex-1">
                <v-textarea v-model="editedInputs[input.name].value" :error-messages="errors" dense outlined
                            single-line type="text" auto-grow rows="1"/>
              </ValidationProvider>
              <ValidationProvider v-else-if="input.type === 'bool'" v-slot="{ errors }" mode="eager" name="input"
                                  rules="required" class="flex-1">
                <v-switch v-model="editedInputs[input.name].value"
                          :error-messages="errors"
                          :label="editedInputs[input.name].value ? 'True' : 'False'"></v-switch>
              </ValidationProvider>
            </template>
          </div>

        </v-col>
      </v-row>
    </v-list-item>
  </v-list>
</template>

<script lang="ts" setup>
import DatasetSelector from '@/views/main/utils/DatasetSelector.vue';
import ModelSelector from '@/views/main/utils/ModelSelector.vue';
import {computed, onMounted, ref, watch} from 'vue';
import {FunctionInputDTO, TestFunctionDTO} from '@/generated-sources';
import {storeToRefs} from 'pinia';
import {useTestSuiteStore} from '@/stores/test-suite';
import {chain} from "lodash";
import {$vfm} from "vue-final-modal";
import CreateAliasModal from "@/views/main/project/modals/CreateAliasModal.vue";
import SlicingFunctionSelector from "@/views/main/utils/SlicingFunctionSelector.vue";
import TransformationFunctionSelector from "@/views/main/utils/TransformationFunctionSelector.vue";
import KwargsCodeEditor from "@/views/main/utils/KwargsCodeEditor.vue";
import {ParsedDocstring} from "@/utils/python-doc.utils";

const props = defineProps<{
  testInputs?: { [key: string]: FunctionInputDTO },
  test?: TestFunctionDTO,
  projectId: number,
  inputs: { [name: string]: string },
  modelValue?: { [name: string]: FunctionInputDTO }
  doc?: ParsedDocstring
}>();

const emit = defineEmits(['invalid', 'result']);

const {models, datasets, suite} = storeToRefs(useTestSuiteStore());

const editedInputs = ref<{ [input: string]: FunctionInputDTO }>({});

function onSuiteInputSelected(name: string) {
  editedInputs.value = {
    ...editedInputs.value,
    [name]: {
      isAlias: true,
      name,
      type: props.inputs[name],
      value: name,
      params: []
    }
  }
}

const inputTypeSelector = [{
  name: 'Suite input',
  description: 'Input to be defined at the execution time of the suite',
  isSelected: (name: string) => !editedInputs.value.hasOwnProperty(name) || editedInputs.value[name].isAlias,
  select: (name: string) => onSuiteInputSelected(name)
}, {
  name: 'Fixed value',
  description: 'Constant value defined before a suite is executed',
  isSelected: (name: string) => editedInputs.value.hasOwnProperty(name) && !editedInputs.value[name].isAlias,
  select: (name: string) => {
    editedInputs.value = {
      ...editedInputs.value,
      [name]: {
        isAlias: false,
        name,
        type: props.inputs[name],
        value: null,
        params: []
      }
    }
  }
}]

function updateEditedValue() {
  editedInputs.value = {
    ...props.modelValue
  }

  Object.keys(props.inputs)
      .filter(inputName => !editedInputs.value.hasOwnProperty(inputName))
      .forEach(inputName => onSuiteInputSelected(inputName));
}

onMounted(() => {
  updateEditedValue();
});


watch(() => props.modelValue, () => updateEditedValue(), {deep: true})

const inputs = computed(() => Object.keys(props.inputs).map((name) => ({
  name,
  type: props.inputs[name]
})));

const buttonToggleValues = ref<{ [name: string]: any }>({});

const aliases = computed(() => {
  return chain([
    ...chain(suite.value!.tests)
        .flatMap(test => Object.values(test.functionInputs))
        .filter(input => input.isAlias)
        .value(),
    ...chain(Object.values(editedInputs.value))
        .filter(input => input.isAlias)
        .value()
  ])
      .groupBy('type')
      .mapValues(v => chain(v)
          .map('value')
          .uniq()
          .value())
      .value()
})

watch(() => [editedInputs.value, props.inputs], () => {
  if (editedInputs.value) {
    buttonToggleValues.value = chain(props.inputs)
        .mapValues((_, name) => inputTypeSelector.find(type => type.isSelected(name)))
        .value();
  } else {
    buttonToggleValues.value = {};
  }
}, {deep: true});

async function createAlias(name: string, type: string) {
  await $vfm.show({
    component: CreateAliasModal,
    bind: {
      name,
      type
    },
    on: {
      async save(input: FunctionInputDTO) {
        editedInputs.value[name] = input;
        editedInputs.value = {...editedInputs.value};
      }
    }
  });
}


watch(() => [editedInputs.value, buttonToggleValues], () => {
  emit('result', editedInputs.value);
  emit('invalid', Object.values(editedInputs.value)
      .findIndex(param => {
            let isOptional = props.test?.args.find(a => a.name === param.name)?.optional;
            return param && !isOptional && (param.value === null || param.value?.trim() === '');
          }
      ) !== -1);
}, {deep: true})


</script>

<style lang="scss" scoped>
.shared-switch {
  width: 150px;
}

.flex-1 {
  flex: 1;
}
</style>
