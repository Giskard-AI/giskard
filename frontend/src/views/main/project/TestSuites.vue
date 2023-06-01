<template>
    <v-container fluid class="vc" v-if="testSuites.length > 0">
        <div class="d-flex flex-row-reverse pb-4">
            <v-btn
                    color="primary"
                    @click="createTestSuite"
            >
                New test suite
            </v-btn>
        </div>
        <v-row>
            <v-card elevation="2"
                    :to="{name: 'test-suite-overview', params: {suiteId: suite.id}}"
                    class="ma-2"
                    style="width: 300px"
                    v-for="suite in testSuites">
                <v-card-title>{{ suite.name }}</v-card-title>
                <v-card-subtitle>Tests: {{ suite.tests.length }}</v-card-subtitle>
                <v-card-text>{{ suite.projectKey }}</v-card-text>
            </v-card>
        </v-row>
    </v-container>
    <v-container v-else class="d-flex flex-column vc fill-height">
        <h1 class="pt-16">You haven't created any test suite for this project!</h1>
        <v-btn tile class='mx-1'
               @click="createTestSuite"
               color="primary">
            <v-icon>add</v-icon>
            Create a new test suite
        </v-btn>
  </v-container>
</template>

<script lang="ts" setup>

import {api} from "@/api";
import {onMounted} from "vue";
import router from '@/router';
import {useTestSuitesStore} from "@/stores/test-suites";
import {storeToRefs} from "pinia";

const props = defineProps<{
    projectId: number
}>();


const testSuitesStore = useTestSuitesStore();
const {testSuites} = storeToRefs(testSuitesStore);

onMounted(async () => await testSuitesStore.loadTestSuites(props.projectId))

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
    await router.push({name: 'test-suite-overview', params: {suiteId: suite.toString()}});
}

</script>
