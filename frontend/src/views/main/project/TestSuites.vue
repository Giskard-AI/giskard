<template>
    <div class="vertical-container">
        <v-container fluid class="vc" v-if="testSuitesStore.testSuites.length > 0">
            <div v-if="testSuitesStore.currentTestSuiteId === null">
                <v-row>
                    <v-col cols="4">
                        <v-text-field label="Search for a test suite" append-icon="search" outlined v-model="searchSession"></v-text-field>
                    </v-col>
                    <v-col cols="8">
                        <div class="d-flex justify-end flex-wrap">
                            <v-btn class="ml-2 mb-2" color="primary" @click="createTestSuite">
                                <v-icon left>mdi-plus</v-icon>
                                create a new suite
                            </v-btn>
                            <v-btn class="ml-2 mb-2" href="https://docs.giskard.ai/en/latest/guides/test-suite/index.html" target="_blank">
                                add suite with code
                                <v-icon right>mdi-open-in-new</v-icon>
                            </v-btn>
                        </div>
                    </v-col>
                </v-row>

                <v-expansion-panels>
                    <v-row class="mr-12 ml-6 caption secondary--text text--lighten-3 pb-2">
                        <v-col cols="3">Suite name</v-col>
                        <v-col cols="2">Last execution</v-col>
                        <v-col cols="2">Tests info</v-col>
                        <v-col cols="2">Status</v-col>
                        <v-col cols="2">Total executions</v-col>
                        <v-col cols="1"></v-col>

                    </v-row>

                    <v-expansion-panel v-for="(suite, index) in filteredSuites" :key="suite.suite.id" @click.stop="openTestSuite(suite.suite.id)" class="expansion-panel">
                        <v-expansion-panel-header :disableIconRotate="true" class="grey lighten-5" tile>
                            <v-row class="px-2 py-1 align-center">
                                <v-col cols="3" class="font-weight-bold">
                                    <div class="pr-4">
                                        <InlineEditText :text="suite.suite.name" @save="(name) => renameSuite(suite.suite.id, name)">
                                        </InlineEditText>
                                    </div>
                                </v-col>
                                <v-col cols="2">
                                    <span v-if="latestExecutions[index]?.executionDate">{{ latestExecutions[index]?.executionDate | date }}</span>
                                    <span v-else>Never</span>
                                </v-col>
                                <v-col cols="2">
                                    <div class="d-flex flex-column">
                                        <span class="font-weight-bold">{{ suite.suite.tests.length }} tests in total</span>
                                        <div v-if="latestExecutions[index]?.executionDate" class="d-flex flex-column">
                                            <span class="passed-tests">{{
                                                latestExecutions[index]?.results?.filter(result => result.status === TestResult.PASSED).length
                                            }} passing</span>
                                            <span class="failed-tests">{{
                                                latestExecutions[index]?.results?.filter(result => result.status === TestResult.FAILED).length
                                            }} failing</span>
                                            <span class="error-tests">{{
                                                latestExecutions[index]?.results?.filter(result => result.status === TestResult.ERROR).length
                                            }} with error</span>
                                        </div>
                                    </div>
                                </v-col>
                                <v-col cols="2">
                                    <div v-if="latestExecutions[index]?.result === 'PASSED'" class="passed-tests font-weight-bold d-flex">
                                        <v-icon small class="mr-1 success-icon">done</v-icon>
                                        <span>PASSING</span>
                                    </div>
                                    <div v-else-if="latestExecutions[index]?.result === 'FAILED'" class="failed-tests font-weight-bold d-flex">
                                        <v-icon small class="mr-1 failed-icon">close</v-icon>
                                        <span>FAILING</span>
                                    </div>
                                    <span v-else class="font-weight-bold">NOT EXECUTED</span>
                                </v-col>
                                <v-col cols="2">
                                    <!-- total number of executions -->
                                    <span v-if="testSuitesStore.testSuitesComplete[index].executions.length">{{ testSuitesStore.testSuitesComplete[index].executions.length }} execution{{ testSuitesStore.testSuitesComplete[index].executions.length > 1 ? 's' : '' }}</span>
                                    <span v-else>None</span>
                                </v-col>
                                <v-col cols="1">
                                    <v-card-actions>
                                        <v-btn icon @click.stop.prevent="deleteTestSuite(suite.suite)">
                                            <v-icon color="accent">delete</v-icon>
                                        </v-btn>
                                    </v-card-actions>
                                </v-col>
                            </v-row>
                        </v-expansion-panel-header>
                    </v-expansion-panel>
                    <div class="d-flex flex-column align-center justify-center mt-6">
                        <v-btn small @click="refresh" plain>
                            <span class="caption">Refresh</span>
                            <v-icon size="small" class="ml-1">refresh</v-icon>
                        </v-btn>
                    </div>
                </v-expansion-panels>

            </div>
            <div v-else>
                <router-view />
            </div>

        </v-container>
        <v-container v-else-if="projectArtifactsStore.datasets.length > 0 && projectArtifactsStore.models.length > 0" class="vc mt-6 fill-height">
            <v-alert class="text-center">
                <p class="headline font-weight-medium grey--text text--darken-2">You haven't created any test suite for this project. <br>Please create a new one.</p>
            </v-alert>
            <div>
                <v-btn @click="createTestSuite" color="primary">
                    <v-icon left>mdi-monitor-shimmer</v-icon>
                    Create a test suite with <span class="font-weight-black ml-1">UI</span>
                </v-btn>
                <span class="mx-4 font-weight-medium grey--text text--darken-2">OR</span>
                <v-btn href="https://docs.giskard.ai/en/latest/guides/test-suite/index.html" target="_blank">
                    <v-icon left>mdi-application-brackets-outline</v-icon>
                    Create a test suite with <span class="font-weight-black ml-1">code</span>
                    <v-icon right class="ml-4">mdi-open-in-new</v-icon>
                </v-btn>


            </div>
            <div class="d-flex justify-center mb-6">
                <img src="@/assets/logo_test_suite.png" class="test-suite-logo" title="Test suite tab logo" alt="A turtle checking a to-do list">
            </div>
            <div class="d-flex flex-column align-center justify-center mt-6">
                <v-btn small @click="refresh" plain>
                    <span class="caption">Refresh</span>
                    <v-icon size="small" class="ml-1">refresh</v-icon>
                </v-btn>
            </div>
        </v-container>
        <v-container v-else-if="apiAccessToken && apiAccessToken.id_token">
            <div class="mt-2">
                <v-alert class='text-center mt-6' v-if="toggleSnippetType === undefined">
                    <p class='headline font-weight-medium grey--text text--darken-2'>There are no artifacts (datasets and models) in this project yet. <br>Choose an option below to upload them and create a test suite.</p>
                </v-alert>

                <div class="d-flex justify-center mt-2">
                    <v-card width="275" outlined :class="{
                        'mx-2': true,
                        'active-option': toggleSnippetType === 'demo',
                        'option-card': true,
                        'd-flex': true,
                        'align-center': true
                    }" @click="openDemoInstructions">
                        <v-card-text class="text-center text-body-1">Upload a test suite from <span class="font-weight-bold">demo projects</span></v-card-text>
                    </v-card>
                    <v-card width="275" outlined :class="{
                        'mx-2': true,
                        'active-option': toggleSnippetType === 'custom',
                        'option-card': true,
                        'd-flex': true,
                        'align-center': true
                    }" @click="openCustomInstructions">
                        <v-card-text class="text-center text-body-1">Upload a test suite from <span class="font-weight-bold">your own model</span></v-card-text>
                    </v-card>
                </div>
            </div>

            <div v-if="toggleSnippetType === 'demo'" class="mt-12 mb-6">
                <p class="text-center">Execute the following Python code with <span class="font-weight-bold">Titanic example</span> to upload a demo test suite to the current project. <br>To upload other demo ML projects, visit our<a href="https://docs.giskard.ai/en/latest/tutorials/tasks/index.html" target="_blank" rel="noopener" class="font-weight-bold text-body-1 ml-1">example page</a>.</p>
                <div class="mt-6 mb-6">
                    <CodeSnippet :codeContent="codeContent" :language="'python'"></CodeSnippet>
                </div>
            </div>
            <div v-else-if="toggleSnippetType === 'custom'" class="mt-12 mb-6 d-flex justify-center">
                <div>
                    <p class="text-center">To upload a <span class="font-weight-bold">test suite from your own model</span>, follow these steps:</p>
                    <v-card max-width="500" class="mt-6 mb-4 card-step" outlined href="https://docs.giskard.ai/en/latest/guides/wrap_dataset/index.html" target="_blank">
                        <v-card-title class="font-weight-medium">
                            <v-icon class="mr-2" color="primary">mdi-numeric-1-circle-outline</v-icon>
                            <span>Wrap your dataset</span>
                            <v-spacer></v-spacer>
                            <v-icon right>mdi-arrow-right</v-icon>
                        </v-card-title>
                        <v-card-text>
                            To scan, test and debug your model, you need to provide a dataset that can be executed by your model. This dataset can be your training, testing, golden, or production dataset.
                        </v-card-text>
                    </v-card>
                    <div class="d-flex justify-center">
                        <div class="dashed-vertical-line"></div>
                    </div>

                    <v-card max-width="500" class="my-4 card-step" outlined href="https://docs.giskard.ai/en/latest/guides/wrap_model/index.html" target="_blank">
                        <v-card-title class="font-weight-medium">
                            <v-icon class="mr-2" color="primary">mdi-numeric-2-circle-outline</v-icon>
                            <span>Wrap your model</span>
                            <v-spacer></v-spacer>
                            <v-icon right>mdi-arrow-right</v-icon>
                        </v-card-title>
                        <v-card-text>
                            To scan, test and debug your model, you need to wrap it into a Giskard Model.
                            Your model can use any ML library and can be any Python function that respects the right signature.
                        </v-card-text>
                    </v-card>
                    <div class="d-flex justify-center">
                        <div class="dashed-vertical-line"></div>
                    </div>
                    <v-card max-width="500" class="mt-4 mb-6 card-step" outlined href="https://docs.giskard.ai/en/latest/guides/scan/index.html" target="_blank">
                        <v-card-title class="font-weight-medium">
                            <v-icon class="mr-2" color="primary">mdi-numeric-3-circle-outline</v-icon>
                            <span>Upload suite from scan</span>
                            <v-spacer></v-spacer>
                            <v-icon right>mdi-arrow-right</v-icon>
                        </v-card-title>
                        <v-card-text>
                            The Giskard python package provides an automatic scan functionality designed to automatically detect potential issues affecting your ML model.
                        </v-card-text>
                    </v-card>
                </div>
            </div>
            <div v-else class="d-flex justify-center my-6">
                <img src="@/assets/logo_test_suite.png" class="test-suite-logo" title="Test suite tab logo" alt="A turtle checking a to-do list">
            </div>
            <div class="d-flex flex-column align-center justify-center mt-6">
                <v-btn small @click="refresh" plain>
                    <span class="caption">Refresh</span>
                    <v-icon size="small" class="ml-1">refresh</v-icon>
                </v-btn>
            </div>
        </v-container>
    </div>
</template>

<script lang="ts" setup>
import { api } from '@/api';
import { apiURL } from '@/env';
import { computed, onActivated, ref } from 'vue';
import router from '@/router';
import { useMainStore } from '@/stores/main';
import { useTestSuitesStore } from '@/stores/test-suites';
import { TYPE } from 'vue-toastification';
import InlineEditText from '@/components/InlineEditText.vue';
import { $vfm } from 'vue-final-modal';
import ConfirmModal from '@/views/main/project/modals/ConfirmModal.vue';
import mixpanel from 'mixpanel-browser';
import CodeSnippet from '@/components/CodeSnippet.vue';
import { JWTToken, TestResult } from '@/generated-sources';
import { useProjectStore } from '@/stores/project';
import { useProjectArtifactsStore } from '@/stores/project-artifacts';

const projectStore = useProjectStore();
const testSuitesStore = useTestSuitesStore();
const projectArtifactsStore = useProjectArtifactsStore();

const props = defineProps<{
    projectId: number
}>();

const searchSession = ref("");
const toggleSnippetType = ref<string | undefined>(undefined);
const apiAccessToken = ref<JWTToken | null>(null);

const codeContent = computed(() => {
    return `import giskard

# Replace this with your own data & model creation.
df = giskard.demo.titanic_df()
data_preprocessing_function, clf = giskard.demo.titanic_pipeline()

# Wrap your Pandas DataFrame
giskard_dataset = giskard.Dataset(df=df,
                                  target="Survived",
                                  name="Titanic dataset",
                                  cat_columns=['Pclass', 'Sex', "SibSp", "Parch", "Embarked"])

# Wrap your model
def prediction_function(df):
    preprocessed_df = data_preprocessing_function(df)
    return clf.predict_proba(preprocessed_df)

giskard_model = giskard.Model(model=prediction_function,
                              model_type="classification",
                              name="Titanic model",
                              classification_labels=clf.classes_,
                              feature_names=['PassengerId', 'Pclass', 'Name', 'Sex', 'Age', 'SibSp', 'Parch', 'Fare', 'Embarked'])

# Then apply the scan
results = giskard.scan(giskard_model, giskard_dataset)

# Create a Giskard client
token = "${apiAccessToken.value?.id_token}" # API Access Token
client = giskard.GiskardClient(url="${apiURL}",  # URL of your Giskard instance
                               token=token)

# Upload an automatically created test suite to the current project ✉️
results.generate_test_suite("Test suite created by scan").upload(client, "${project.value!.key}")
`
});

const project = computed(() => {
    return projectStore.project(props.projectId)
});

const filteredSuites = computed(() => {
    return testSuitesStore.testSuitesComplete.filter(suite => suite.suite.name.toLowerCase().includes(searchSession.value.toLowerCase()));
});

const latestExecutions = computed(() => {
    const executions = filteredSuites.value.map(suite => suite.executions);
    return executions.map(executionsSuite => executionsSuite.length === 0 ? null : executionsSuite[0]);
});

async function createTestSuite() {
    const project = await api.getProject(props.projectId)


    const suite = await api.createTestSuite(project.key, {
        id: null,
        name: `Unnamed test suite`,
        projectKey: project.key,
        functionInputs: [],
        tests: []
    });

    mixpanel.track('Create test suite',
        {
            id: suite,
            projectKey: project.key,
            screen: 'project-testing'
        }
    );

    await testSuitesStore.reload()
    await router.push({ name: 'project-testing-test-suite-overview', params: { suiteId: suite.toString() } });
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
        name: 'project-testing-test-suite-overview',
        params: {
            projectId,
            suiteId
        }
    });
}

async function renameSuite(suiteId: number, name: string) {
    const currentSuite = testSuitesStore.testSuites.find(s => s.id === suiteId);

    if (currentSuite) {
        currentSuite.name = name;
        await testSuitesStore.updateSuiteName(currentSuite);
        mixpanel.track('Renamed test suite', { suiteId });
    }
}

function deleteTestSuite(suite: any) {
    $vfm.show({
        component: ConfirmModal,
        bind: {
            title: 'Delete test suite',
            text: `Are you sure that you want to delete the test suite '${suite.name}'?`,
            isWarning: true
        },
        on: {
            async confirm(close) {
                await api.deleteSuite(suite.projectKey!, suite.id!);
                await testSuitesStore.reloadComplete();
                close();
                useMainStore().addNotification({
                    content: `The test suite '${suite.name}' has been deleted.`,
                    color: TYPE.SUCCESS,
                    showProgress: false
                });

                mixpanel.track('Delete test suite',
                    {
                        id: suite.id,
                        projectKey: suite.projectKey,
                        screen: 'project-testing'
                    });
            }
        }
    });
}

const generateApiAccessToken = async () => {
    try {
        apiAccessToken.value = await api.getApiAccessToken();
    } catch (error) {
        console.log(error);
    }
}

async function refresh() {
    await testSuitesStore.reloadComplete();
    await projectArtifactsStore.loadProjectArtifacts(false);
}

function openDemoInstructions() {
    toggleSnippetType.value = 'demo';
    mixpanel.track('Select option to upload test suite', {
        projectKey: project.value!.key,
        option: 'demo',
        screen: 'project-testing'
    });
}

function openCustomInstructions() {
    toggleSnippetType.value = 'custom';
    mixpanel.track('Select option to upload test suite', {
        projectKey: project.value!.key,
        option: 'custom',
        screen: 'project-testing'
    });
}

onActivated(async () => {
    searchSession.value = "";
    if (testSuitesStore.currentTestSuiteId !== null) {
        await redirectToTestSuite(props.projectId.toString(), testSuitesStore.currentTestSuiteId.toString());
    } else {
        await testSuitesStore.loadTestSuites(props.projectId);
        await testSuitesStore.loadTestSuiteComplete(props.projectId);
        await projectArtifactsStore.setProjectId(props.projectId, false);
    }
    await generateApiAccessToken();
})
</script>

<style scoped>
.test-suite-logo {
    height: max(50vh, 150px);
    margin-top: 2rem;

}

.expansion-panel {
    margin-top: 10px !important;
}

.success-icon {
    color: #66AD5B;
}

.failed-icon {
    color: #EB5E59;
}

.passed-tests {
    margin-top: 0.25rem;
    color: #66AD5B;
}

.failed-tests {
    margin-top: 0.25rem;
    color: #EB5E59;
}

.error-tests {
    margin-top: 0.25rem;
    color: #ebba59;
}

.option-card {
    border: 2px solid rgba(0, 0, 0, 0.2);
}

.option-card:hover {
    cursor: pointer;
    transition: background-color 0.5s ease;
    background-color: rgba(0, 0, 0, 0.1);
}


.active-option {
    border: 2px solid #087038;
    background-color: rgba(8, 112, 56, 0.07)
}

.active-option .v-card__text {
    color: #087038;
}

.card-step:hover {
    cursor: pointer;
    /* change background color with animation */
    transition: background-color 0.5s ease;
    background-color: rgba(8, 112, 56, 0.07);
}

.card-step:hover .v-icon {
    color: #087038;
}

.dashed-vertical-line {
    display: inline-block;
    border-left: 2px dashed rgba(0, 0, 0, 0.15);
    height: 50px;
    margin: 0 auto;
}
</style>
