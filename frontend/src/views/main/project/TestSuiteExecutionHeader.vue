<template>
    <div class="d-flex w100 align-start">
        <v-alert prominent :icon="testResultStyle.icon" outlined text :color="testResultStyle.color"
                 class="flex-grow-1">
            <v-row align="center">
                <v-col class="grow">
                    <h4 v-if="!props.execution">
                        No execution has been performed yet!
                    </h4>
                    <h4 v-else-if="props.execution.result === TestResult.ERROR">
                        An error arose during the execution. Check the <span @click="openLogs" class="clickable">execution logs.</span>
                    </h4>
                    <h4 v-else>Test suite
                        {{ props.execution.result === TestResult.PASSED ? 'passed' : 'failed' }}:
                        <span v-if="successRatio.failed > 0">{{ plurialize('test', successRatio.failed) }} failed</span>
                        <span v-if="successRatio.failed > 0 && successRatio.passed > 0">, </span>
                        <span v-if="successRatio.passed > 0">{{ plurialize('test', successRatio.passed) }} passed</span>
                        <span v-if="successRatio.failed > 0 || successRatio.passed > 0">. </span>
                        Check the <span @click="openLogs" class="clickable">execution logs.</span>
                    </h4>
                </v-col>
            </v-row>
        </v-alert>
        <v-btn icon @click="openSettings" color="secondary" v-if="!compact">
            <v-icon>settings</v-icon>
        </v-btn>
    </div>
</template>

<script setup lang="ts">

import {SuiteTestDTO, SuiteTestExecutionDTO, TestResult, TestSuiteExecutionDTO} from '@/generated-sources';
import {computed} from 'vue';
import {api} from '@/api';
import {$vfm} from 'vue-final-modal';
import ExecutionLogsModal from '@/views/main/project/modals/ExecutionLogsModal.vue';
import {storeToRefs} from 'pinia';
import {useTestSuiteStore} from '@/stores/test-suite';
import EditTestSuiteModal from "@/views/main/project/modals/EditTestSuiteModal.vue";
import {plurialize} from "../../../utils/string.utils";
import {Colors} from "@/utils/colors";

const props = defineProps<{
    tests: {
        suiteTest: SuiteTestDTO
        result?: SuiteTestExecutionDTO
    }[],
    execution?: TestSuiteExecutionDTO,
    compact: boolean
}>();

const {suite, projectId} = storeToRefs(useTestSuiteStore());

const testResultStyle = computed(() => {
    if (!props.execution) {
        return {
            icon: 'block',
            color: 'dark-grey'
        }
    }
    switch (props.execution.result) {
        case TestResult.PASSED:
            return {
                icon: 'done',
                color: Colors.PASS
            }
        case TestResult.FAILED:
            return {
                icon: 'close',
                color: Colors.FAIL
            }
        default:
            return {
                icon: 'error',
                color: Colors.FAIL
            }
    }
})

const successRatio = computed(() => ({
    passed: executedTests.value.filter(({result}) => result!.passed).length,
    failed: executedTests.value.filter(({result}) => !result!.passed).length
}))

const executedTests = computed(() => !props.execution || props.execution.result === TestResult.ERROR ? []
    : props.tests.filter(({result}) => result !== undefined));

async function openSettings() {
    const project = await api.getProject(projectId.value!)
    $vfm.show({
        component: EditTestSuiteModal,
        bind: {
            projectKey: project.key,
            projectId: project.id,
            suite: suite.value
        }
    });
}

function openLogs() {
    $vfm.show({
        component: ExecutionLogsModal,
        bind: {
            logs: props.execution?.logs
        }
    });
}
</script>

<style scoped lang="scss">
.clickable {
    cursor: pointer;
    text-decoration: underline;
}
</style>

