<template>
    <div class="pt-3">
        <v-form @submit.prevent="">
            <ValidationObserver ref="observer" v-slot="{ invalid }">
                <v-row>
                    <v-col cols=12>
                        <ValidationProvider name="test suite name" rules="required" v-slot="{errors}">
                            <v-text-field label="Test suite name" autofocus v-model="name"
                                          :error-messages="errors"
                                          outlined></v-text-field>
                        </ValidationProvider>
                    </v-col>
                </v-row>

                <v-divider></v-divider>

                <div class="flex">
                    <div class="flex-grow-1"/>
                    <v-btn
                        color="error"
                        text
                        @click="deleteSuite(close)"
                    >
                        Delete suite
                    </v-btn>
                    <v-btn
                        color="primary"
                        text
                        @click="submit(close)"
                        :disabled="invalid || invalidInputs"
                        :loading="isLoading"
                    >
                        Update
                    </v-btn>
                </div>
            </ValidationObserver>
        </v-form>
    </div>
</template>

<script lang="ts" setup>

import {computed, onMounted, ref} from "vue";
import {useRouter} from "vue-router/composables";
import {useTestSuiteStore} from "@/stores/test-suite";
import {FunctionInputDTO} from "@/generated-sources";
import {useTestSuitesStore} from "@/stores/test-suites";
import {chain} from "lodash";
import {$vfm} from "vue-final-modal";
import ConfirmModal from "@/views/main/project/modals/ConfirmModal.vue";
import {api} from "@/api";
import {storeToRefs} from "pinia";

const props = defineProps<{
    projectId: number,
    suiteId: number
}>();

const {suite, projectId} = storeToRefs(useTestSuiteStore())

const dialog = ref<boolean>(false);
const name = ref<string>('');
const isLoading = ref<boolean>(false);
const showAdvancedSettings = ref<boolean>(false);

const router = useRouter();
const {updateTestSuite, inputs} = useTestSuiteStore();

const editedInputs = ref<{ [input: string]: FunctionInputDTO }>({});
const invalidInputs = ref(false);
const result = ref<{ [input: string]: FunctionInputDTO }>({});
const testSuitesStore = useTestSuitesStore();

const inputTypes = computed(() => Object.entries(inputs)
    .reduce((result, [name, {type}]) => {
        result[name] = type;
        return result;
    }, {})
);

onMounted(() => {
    if (suite.value) {
        name.value = suite.value.name;
        editedInputs.value = chain(suite.value.functionInputs)
            .keyBy('name')
            .mapValues(v => ({...v}))
            .value()
    }
})

async function submit(close) {
    isLoading.value = true;

    await updateTestSuite(suite.value!.projectKey!, {
        ...suite.value!,
        name: name.value,
        functionInputs: Object.values(result.value)
    }).finally(() => isLoading.value = false);

    dialog.value = false;
    close();
}


async function deleteSuite(outerClose) {
    await $vfm.show({
        component: ConfirmModal,
        bind: {
            title: `Delete '${suite.value!.name}'`,
            text: `Are you sure that you want to delete '${suite.value!.name}' forever?`,
            isWarning: true
        },
        on: {
            async confirm(close) {
                await api.deleteSuite(suite.value!.projectKey!, suite.value!.id!);
                await testSuitesStore.reload()
                await router.push({
                    name: 'project-test-suites'
                })
                close();
                outerClose();
            }
        }
    });
}

</script>


<style scoped lang="scss">
.main-container {
    width: 100%;
    max-width: 100%;
    color: rgb(98, 98, 98);

    b {
        color: black;
    }
}

.parent-container {
    margin-left: -12px;
    margin-right: -12px;
}

.overview-container {
    background-color: #f5f5f5;
}

.test-suite-name {
    color: rgb(32, 57, 48);
}

.max-w-200 {
    max-width: 200px;
}
</style>
