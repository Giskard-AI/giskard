<template>
    <v-list>
        <v-list-item v-for="input in inputs" :track-by="input" class="pl-0 pr-0">
            <v-row>
                <v-col cols="3">
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
                <v-col cols="3">
                    <v-btn-toggle
                            v-model="buttonToggleValues[input.name]"
                            @change="item => handleTypeSelected(input.name, item)">
                        <v-tooltip bottom>
                            <template v-slot:activator="{ on, attrs }">
                                <v-btn v-on="on" v-bind="attrs">
                                    <span class="hidden-sm-and-down">Input</span>
                                    <v-icon right>input</v-icon>
                                </v-btn>
                            </template>
                            <span>Set as a suite input</span>
                        </v-tooltip>
                        <v-tooltip bottom>
                            <template v-slot:activator="{ on, attrs }">
                                <v-btn v-on="on" v-bind="attrs">
                                    <span class="hidden-sm-and-down">Alias</span>
                                    <v-icon right>link</v-icon>
                                </v-btn>
                            </template>
                            <span>Set an alias to this input</span>
                        </v-tooltip>
                    </v-btn-toggle>
                </v-col>
                <v-col cols="6">
                    <template v-if="!editing">
                        <span v-if="!props.testInputs.hasOwnProperty(input.name)" class="font-italic">
                          Suite input
                        </span>
                        <span v-if="props.testInputs[input.name]?.isAlias">
                    {{ props.testInputs[input.name].value }}
                  </span>
                        <span v-else-if="input.name in props.testInputs && input.type === 'Model'">
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
                      <span v-if="!props.modelValue.hasOwnProperty(input.name)" class="font-italic">
                        Suite input
                      </span>
                        <template v-else-if="!props.modelValue[input.name].isAlias">
                            <DatasetSelector :project-id="projectId" :label="input.name" :return-object="false"
                                             v-if="input.type === 'Dataset'"
                                             :value.sync="props.modelValue[input.name].value"/>
                            <ModelSelector :project-id="projectId" :label="input.name" :return-object="false"
                                           v-else-if="input.type === 'Model'"
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
                    </div>

                </v-col>
            </v-row>
        </v-list-item>
    </v-list>
</template>

<script setup lang="ts">
import DatasetSelector from '@/views/main/utils/DatasetSelector.vue';
import ModelSelector from '@/views/main/utils/ModelSelector.vue';
import {computed, ref, watch} from 'vue';
import {TestFunctionDTO, TestInputDTO} from '@/generated-sources';
import {storeToRefs} from 'pinia';
import {useTestSuiteStore} from '@/stores/test-suite';
import {chain} from "lodash";

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


const buttonToggleValues = ref<{ [name: string]: number | null }>({});

watch(() => [props.modelValue, props.inputs], () => {
    if (props.modelValue) {
        buttonToggleValues.value = chain(props.inputs)
            .mapValues((_, name) => {
                console.log(name, props.modelValue)
                if (!props.modelValue!.hasOwnProperty(name)) {
                    return 0;
                } else if (props.modelValue![name].isAlias) {
                    return 1;
                } else {
                    return null;
                }
            })
            .value();
    } else {
        buttonToggleValues.value = {};
    }
}, {deep: true})

function handleTypeSelected(input: string, item: number) {
    switch (item) {
        case 0:
            delete props.modelValue![input];
            break;
        case 1:
            props.modelValue![input] = {
                isAlias: true,
                name: input,
                type: props.inputs[input],
                value: null
            };
            break;
        default:
            props.modelValue![input] = {
                isAlias: false,
                name: input,
                type: props.inputs[input],
                value: null
            };
            break;
    }
}

</script>

<style scoped lang="scss">


.shared-switch {
  width: 150px;
}
</style>
