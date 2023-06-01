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
                <v-col>
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
                        <span v-else-if="input && input.name in props.testInputs">{{
                            props.testInputs[input.name].value
                            }}</span>
                    </template>
                    <div v-else-if="props.modelValue" class="d-flex">
                        <template v-if="!props.modelValue[input.name].isAlias">
                            <DatasetSelector :project-id="projectId" :label="input.name" :return-object="false"
                                             v-if="input.type === 'Dataset'"
                                             :value.sync="props.modelValue[input.name].value"/>
                            <ModelSelector :project-id="projectId" :label="input.name" :return-object="false"
                                           v-else-if="input.type === 'BaseModel'"
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
                        <v-select
                                v-else
                                clearable
                                outlined
                                v-model="props.modelValue[input.name].value"
                                :items="sharedInputs.filter(i => i.type === input.type)"
                                item-text="name"
                                item-value="name"
                                dense
                                hide-details
                        ></v-select>

                        <div class="shared-switch" v-if="sharedInputs">
                            <v-switch v-if="sharedInputs.filter(i => i.type === input.type).length > 0"
                                      v-model="props.modelValue[input.name].isAlias"
                                      @change="() => props.modelValue[input.name].value = null"
                                      label="Shared input"></v-switch>
                        </div>
                    </div>

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

const props = defineProps<{
    testInputs?: { [key: string]: TestInputDTO },
    test?: TestFunctionDTO,
    projectId: number,
    inputs: { [name: string]: string },
    modelValue?: { [name: string]: TestInputDTO },
    sharedInputs?: Array<TestInputDTO>,
    editing: boolean
}>();

const {models, datasets} = storeToRefs(useTestSuiteStore());

const inputs = computed(() => Object.keys(props.inputs).map((name) => ({
    name,
    type: props.inputs[name]
})));


function linkInput(name: string, link: boolean) {
    props.modelValue![name].value = '';
    props.modelValue![name].isAlias = link;
}

</script>

<style scoped lang="scss">


.shared-switch {
  width: 150px;
}
</style>
