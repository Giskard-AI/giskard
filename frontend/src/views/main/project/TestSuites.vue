<template>
    <v-container fluid class="vc" v-if="testSuites.length > 0">
        <div v-if="testSuitesStore.currentTestSuiteId === null">
            <div class="d-flex flex-row-reverse pb-4">
                <v-btn color="primaryLight" class="primaryLightBtn" @click="createTestSuite">
                    <v-icon left>add</v-icon>
                    New test suite
                </v-btn>
            </div>
            <v-row>
                <v-card elevation="2" @click.stop="openTestSuite(suite.id)" class="ma-2" style="width: 300px" v-for="suite in testSuites" :key="suite.id">
                    <v-card-title>{{ suite.name }}</v-card-title>
                    <v-card-subtitle>Tests: {{ suite.tests.length }}</v-card-subtitle>
                    <v-card-text>{{ suite.projectKey }}</v-card-text>
                </v-card>
            </v-row>
        </div>
        <div v-else>
            <router-view />
        </div>

    </v-container>
    <v-container v-else class="vc mt-6 fill-height">
        <v-alert class="text-center">
            <p class="headline font-weight-medium grey--text text--darken-2">You haven't created any test suite for this project. <br>Please create a new one.</p>
        </v-alert>
        <v-btn tile @click="createTestSuite" color="primaryLight" class="primaryLightBtn">
            <v-icon>add</v-icon>
            Create a new test suite
        </v-btn>
        <div class="d-flex justify-center mb-6">
            <img src="@/assets/logo_test_suite.png" class="test-suite-logo" title="Test suite tab logo" alt="A turtle checking a to-do list">
        </div>
    </v-container>
</template>

<script lang="ts" setup>
import { api } from "@/api";
import { onActivated } from "vue";
import router from '@/router';
import { useTestSuitesStore } from "@/stores/test-suites";
import { storeToRefs } from "pinia";
import { useMainStore } from "@/stores/main";
import { TYPE } from "vue-toastification";

const props = defineProps<{
    projectId: number
}>();


const testSuitesStore = useTestSuitesStore();
const { testSuites } = storeToRefs(testSuitesStore);

async function createTestSuite() {
    const project = await api.getProject(props.projectId)
    const suite = await api.createTestSuite(project.key, {
        id: null,
        name: 'Unnamed test suite',
        projectKey: project.key,
        testInputs: [],
        tests: []
    });

    await testSuitesStore.reload()
    await router.push({ name: 'test-suite-overview', params: { suiteId: suite.toString() } });
}

async function openTestSuite(suiteId: number | null | undefined) {
    if (!suiteId) {
        useMainStore().addNotification({
            content: 'Test suite not found',
            color: TYPE.ERROR
        });
    }

    testSuitesStore.setCurrentTestSuiteId(suiteId!);
    await redirectToTestSuite(props.projectId.toString(), suiteId!.toString());
}

async function redirectToTestSuite(projectId: string, suiteId: string) {
    await router.push({
        name: 'test-suite-overview',
        params: {
            projectId,
            suiteId
        }
    });
}

onActivated(async () => {
    if (testSuitesStore.currentTestSuiteId !== null) {
        await redirectToTestSuite(props.projectId.toString(), testSuitesStore.currentTestSuiteId.toString());
    } else {
        await testSuitesStore.loadTestSuites(props.projectId);
    }
})

</script>

<style scoped>
.test-suite-logo {
    width: min(17.5vw, 150px);
    margin-top: 2rem;
}
</style>
