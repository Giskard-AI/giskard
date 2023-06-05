<template>
    <vue-final-modal v-slot="{ close }" v-bind="$attrs" classes="modal-container" content-class="modal-content" v-on="$listeners">
        <v-form @submit.prevent="">
            <ValidationObserver ref="observer" v-slot="{ invalid }">
                <v-card>
                    <v-card-title>
                        {{ `Edit ${suite?.name}` }}
                    </v-card-title>

                    <v-card-text>
                        <v-row>
                            <v-col cols=12>
                                <ValidationProvider name="test suite name" rules="required" v-slot="{ errors }">
                                    <v-text-field label="Test suite name" autofocus v-model="name" :error-messages="errors" outlined></v-text-field>
                                </ValidationProvider>
                                <h2 v-if="showAdvancedSettings">Inputs</h2>
                                <TestInputListSelector :model-value="editedInputs" :project-id="projectId" :inputs="inputTypes" @invalid="i => invalidInputs = i" @result="v => result = v" />
                            </v-col>
                        </v-row>
                    </v-card-text>

                    <v-divider></v-divider>

                    <v-card-actions>
                        <v-spacer></v-spacer>
                        <v-btn color="error" text @click="deleteSuite(close)">
                            Delete suite
                        </v-btn>
                        <v-btn color="primary" text @click="submit(close)" :disabled="invalid || invalidInputs" :loading="isLoading">
                            Update
                        </v-btn>
                    </v-card-actions>
                </v-card>
            </ValidationObserver>
        </v-form>
    </vue-final-modal>
</template>

<script setup lang="ts">

import {computed, onMounted, ref} from 'vue';
import {FunctionInputDTO, TestSuiteDTO} from '@/generated-sources';
import {useRouter} from 'vue-router/composables';
import {useTestSuiteStore} from '@/stores/test-suite';
import TestInputListSelector from "@/components/TestInputListSelector.vue";
import {chain} from "lodash";
import {$vfm} from "vue-final-modal";
import {api} from "@/api";
import ConfirmModal from "@/views/main/project/modals/ConfirmModal.vue";
import {useTestSuitesStore} from "@/stores/test-suites";
import mixpanel from "mixpanel-browser";

const {projectKey, projectId, suite} = defineProps<{
    projectKey: string,
    projectId: number
    suite: TestSuiteDTO
}>();

const dialog = ref<boolean>(false);
const name = ref<string>('');
const isLoading = ref<boolean>(false);
const showAdvancedSettings = ref<boolean>(false);

const router = useRouter();
const { updateTestSuite, inputs } = useTestSuiteStore();

const editedInputs = ref<{ [input: string]: FunctionInputDTO }>({});
const invalidInputs = ref(false);
const result = ref<{ [input: string]: FunctionInputDTO }>({});
const testSuitesStore = useTestSuitesStore();

const inputTypes = computed(() => Object.entries(inputs)
    .reduce((result, [name, { type }]) => {
        result[name] = type;
        return result;
    }, {})
);

onMounted(() => {
    if (suite) {
        name.value = suite.name;
        editedInputs.value = chain(suite.functionInputs)
            .keyBy('name')
            .mapValues(v => ({ ...v }))
            .value()
    }
})

async function submit(close) {
    isLoading.value = true;

    await updateTestSuite(projectKey, {
        ...suite,
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
            title: `Delete '${suite.name}'`,
            text: `Are you sure that you want to delete '${suite.name}' forever?`,
            isWarning: true
        },
        on: {
            async confirm(close) {
                await api.deleteSuite(suite.projectKey!, suite.id!);
                testSuitesStore.setCurrentTestSuiteId(null);
                await testSuitesStore.reload()
                await router.push({
                    name: 'project-testing'
                })
                close();
                outerClose();

                mixpanel.track('Delete test suite',
                    {
                        id: suite.id,
                        projectKey: suite.projectKey,
                        screen: 'Edit test suite modal'
                    });
            }
        }
    });
}

</script>

<style scoped>
::v-deep(.modal-container) {
    display: flex;
    justify-content: center;
    align-items: center;
}

::v-deep(.modal-content) {
    position: relative;
    display: flex;
    flex-direction: column;
    margin: 0 1rem;
    padding: 1rem;
    min-width: 50vw;
}
</style>
