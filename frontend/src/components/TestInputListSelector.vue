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
                    <v-select v-model="buttonToggleValues[input.name]"
                              :items="inputTypeSelector"
                              return-object
                              item-text="name"
                              @change="item => item.select(input.name)">
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
                      <span v-if="!editedInputs.hasOwnProperty(input.name)" class="font-italic">
                        Suite input. Provided at the execution time.
                      </span>
                        <template v-else-if="!editedInputs[input.name].isAlias">
                            <DatasetSelector :project-id="projectId" :label="input.name" :return-object="false"
                                             v-if="input.type === 'Dataset'"
                                             :value.sync="editedInputs[input.name].value"/>
                            <ModelSelector :project-id="projectId" :label="input.name" :return-object="false"
                                           v-else-if="input.type === 'BaseModel'"
                                           :value.sync="editedInputs[input.name].value"/>
                            <SliceFunctionSelector :project-id="projectId" :label="input.name" :return-object="false"
                                                   v-else-if="input.type === 'SliceFunction'"
                                                   :value.sync="editedInputs[input.name].value"/>
                            <ValidationProvider
                                name="value"
                                v-else-if="['float', 'int'].includes(input.type)"
                                mode="eager" rules="required" v-slot="{errors}">
                                <v-text-field
                                    :step='input.type === "float" ? 0.1 : 1'
                                    v-model="editedInputs[input.name].value"
                                    :error-messages="errors"
                                    single-line
                                    type="number"
                                    outlined
                                    dense
                                />
                            </ValidationProvider>
                            <ValidationProvider v-else-if="input.type === 'str'"
                                                name="input"
                                                mode="eager" rules="required"
                                                v-slot="{errors}">
                                <v-text-field
                                    v-model="editedInputs[input.name].value"
                                    :error-messages="errors"
                                    single-line
                                    type="text"
                                    outlined
                                    dense
                                />
                            </ValidationProvider>
                        </template>
                        <ValidationProvider v-else name="alias"
                                            mode="eager" rules="required"
                                            v-slot="{errors}">
                            <v-select
                                clearable
                                outlined
                                v-model="editedInputs[input.name].value"
                                :items="aliases[input.type] ?? []"
                                :menu-props="{
                                  closeOnClick: true,
                                  closeOnContentClick: true,
                                }"
                                dense
                                :error-messages="errors"
                            >
                                <template v-slot:prepend-item>
                                    <v-list-item
                                        ripple
                                        @mousedown.prevent
                                        @click="() => createAlias(input.name, input.type)"
                                    >
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
                    </div>

                </v-col>
            </v-row>
        </v-list-item>
    </v-list>
</template>

<script setup lang="ts">
import DatasetSelector from '@/views/main/utils/DatasetSelector.vue';
import ModelSelector from '@/views/main/utils/ModelSelector.vue';
import {computed, onMounted, ref, watch} from 'vue';
import {TestFunctionDTO, TestInputDTO} from '@/generated-sources';
import {storeToRefs} from 'pinia';
import {useTestSuiteStore} from '@/stores/test-suite';
import {chain} from "lodash";
import {$vfm} from "vue-final-modal";
import CreateAliasModal from "@/views/main/project/modals/CreateAliasModal.vue";
import SliceFunctionSelector from "@/views/main/utils/SliceFunctionSelector.vue";

const props = defineProps<{
    testInputs?: { [key: string]: TestInputDTO },
    test?: TestFunctionDTO,
    projectId: number,
    inputs: { [name: string]: string },
    modelValue?: { [name: string]: TestInputDTO }
}>();

const emit = defineEmits(['invalid', 'result']);

const {models, datasets, suite} = storeToRefs(useTestSuiteStore());

const editedInputs = ref<{ [input: string]: TestInputDTO }>({});

const inputTypeSelector = [{
    name: 'Suite input (not shared)',
    description: 'Input to be defined at the execution of the suite',
    isSelected: (name) => !editedInputs.value.hasOwnProperty(name),
    select: (name) => {
        delete editedInputs.value[name];
        editedInputs.value = {
            ...editedInputs.value
        };
    }
}, {
    name: 'Fixed value',
    description: 'Value to be set',
    isSelected: (name) => editedInputs.value.hasOwnProperty(name) && !editedInputs.value[name].isAlias,
    select: (name) => {
        editedInputs.value = {
            ...editedInputs.value,
            [name]: {
                isAlias: false,
                name,
                type: props.inputs[name],
                value: null
            }
        }
    }
}, {
    name: 'Suite input (shared)',
    description: 'Rename of the input name to allow flexibility',
    isSelected: (name) => editedInputs.value.hasOwnProperty(name) && editedInputs.value[name].isAlias,
    select: (name) => {
        editedInputs.value = {
            ...editedInputs.value,
            [name]: {
                isAlias: true,
                name,
                type: props.inputs[name],
                value: null
            }
        }
    }
}, { // TODO
    name: 'Shard value',
    description: 'Value to be set and shared with other tests',
    isSelected: (name) => editedInputs.value.hasOwnProperty(name) && editedInputs.value[name].isAlias,
    select: (name) => {
        editedInputs.value = {
            ...editedInputs.value,
            [name]: {
                isAlias: true,
                name,
                type: props.inputs[name],
                value: null
            }
        }
    }
}]

function updateEditedValue() {
    editedInputs.value = {
        ...props.modelValue
    }
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
            .flatMap(test => Object.values(test.testInputs))
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
            async save(input: TestInputDTO) {
                editedInputs.value[name] = input;
                editedInputs.value = {...editedInputs.value};
            }
        }
    });
}


watch(() => [editedInputs.value, buttonToggleValues], () => {
    emit('result', editedInputs.value);
    emit('invalid', Object.values(editedInputs.value)
        .findIndex(param => param && (param.value === null || param.value.trim() === '')) !== -1);
}, {deep: true})


</script>

<style scoped lang="scss">


.shared-switch {
  width: 150px;
}
</style>
