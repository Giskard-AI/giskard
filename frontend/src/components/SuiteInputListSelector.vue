<template>
    <v-list>
        <v-list-item v-for="input in inputs" :track-by="input" class="pl-0 pr-0">
            <v-row>
                <v-col>
                    <v-list-item-content>
                        <v-list-item-title>{{ input.name }}</v-list-item-title>
                        <v-list-item-subtitle class="text-caption">{{ input.type }}</v-list-item-subtitle>
                        <v-list-item-action-text
                                v-if="props.test && !!props.test.args.find(a => a.name === input.name).optional">
                            Optional. Default:
                            <code>{{ props.test.args.find(a => a.name === input.name).defaultValue }}</code>
                        </v-list-item-action-text>
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
                        <DatasetSelector :project-id="projectId" :label="input.name" :return-object="false"
                                         v-if="input.type === 'Dataset'"
                                         :value.sync="props.modelValue[input.name].value"/>
                        <ModelSelector :project-id="projectId" :label="input.name" :return-object="false"
                                       v-else-if="input.type === 'BaseModel'"
                                       :value.sync="props.modelValue[input.name].value"/>
                        <SlicingFunctionSelector :project-id="projectId" :label="input.name"
                                                 v-else-if="input.type === 'SlicingFunction'"
                                                 :value.sync="props.modelValue[input.name].value"
                                                 :args.sync="props.modelValue[input.name].params"/>
                        <TransformationFunctionSelector :project-id="projectId" :label="input.name"
                                                        v-else-if="input.type === 'TransformationFunction'"
                                                        :value.sync="props.modelValue[input.name].value"
                                                        :args.sync="props.modelValue[input.name].params"/>
                        <v-text-field
                                :step='input.type === "float" ? 0.1 : 1'
                                v-model="props.modelValue[input.name].value"
                                v-else-if="['float', 'int'].includes(input.type)"
                                hide-details
                                single-line
                                type="number"
                                outlined
                                dense
                        />
                        <v-text-field
                                v-model="props.modelValue[input.name].value"
                                v-else-if="input.type === 'str'"
                                hide-details
                                single-line
                                type="text"
                                outlined
                                dense
                        />
                    </template>
                </v-col>
            </v-row>
        </v-list-item>
    </v-list>
</template>

<script setup lang="ts">
import DatasetSelector from '@/views/main/utils/DatasetSelector.vue';
import ModelSelector from '@/views/main/utils/ModelSelector.vue';
import {computed} from 'vue';
import {FunctionInputDTO, TestFunctionDTO} from '@/generated-sources';
import {storeToRefs} from 'pinia';
import {useTestSuiteStore} from '@/stores/test-suite';
import SlicingFunctionSelector from "@/views/main/utils/SlicingFunctionSelector.vue";
import {useCatalogStore} from "@/stores/catalog";
import TransformationFunctionSelector from "@/views/main/utils/TransformationFunctionSelector.vue";

const props = defineProps<{
    functionInputs?: { [key: string]: FunctionInputDTO },
    test?: TestFunctionDTO,
    projectId: number,
    inputs: { [name: string]: string },
    modelValue?: { [name: string]: FunctionInputDTO },
    editing: boolean
}>();

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

</style>
