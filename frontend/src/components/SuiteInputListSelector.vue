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
                      <span v-if="props.testInputs[input.name]?.isAlias">
                        {{ props.testInputs[input.name].value }}
                      </span>
                        <span v-else-if="input.name in props.testInputs && input.type === 'BaseModel'">
                      {{
                            models[props.testInputs[input.name].value].name ?? models[props.testInputs[input.name].value].id
                            }}
                    </span>
                        <span v-else-if="input.name in props.testInputs && input.type === 'Dataset'">
                      {{
                            datasets[props.testInputs[input.name].value].name ?? datasets[props.testInputs[input.name].value].id
                            }}
                          </span>
                        <span v-else-if="input.name in props.testInputs && input.type === 'SliceFunction'">
                      {{
                            sliceFunctionsByUuid[props.testInputs[input.name].value].displayName
                            ?? sliceFunctionsByUuid[props.testInputs[input.name].value].name
                            }}
                    </span>
                        <span v-else-if="input && input.name in props.testInputs">{{
                            props.testInputs[input.name].value
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
                        <SliceFunctionSelector :project-id="projectId" :label="input.name" :return-object="false"
                                               v-else-if="input.type === 'SliceFunction'"
                                               :value.sync="props.modelValue[input.name].value"/>
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
import {TestFunctionDTO, TestInputDTO} from '@/generated-sources';
import {storeToRefs} from 'pinia';
import {useTestSuiteStore} from '@/stores/test-suite';
import SliceFunctionSelector from "@/views/main/utils/SliceFunctionSelector.vue";
import {useCatalogStore} from "@/stores/catalog";

const props = defineProps<{
    testInputs?: { [key: string]: TestInputDTO },
    test?: TestFunctionDTO,
    projectId: number,
    inputs: { [name: string]: string },
    modelValue?: { [name: string]: TestInputDTO },
    editing: boolean
}>();

const {models, datasets} = storeToRefs(useTestSuiteStore());
const {sliceFunctionsByUuid} = storeToRefs(useCatalogStore());

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
