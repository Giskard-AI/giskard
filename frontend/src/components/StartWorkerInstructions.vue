<template>
    <v-card outlined>
        <v-card-text>
            <v-alert class="pa-0 text-body-2" colored-border type="info" icon>
                <p class="mb-0">ML Worker is a python process that allows Giskard to execute models in a user's
                    environment</p>
                <p v-if="appSettings">A worker communicates with the backend through TCP port <code class="font-weight-bold">{{ appSettings.externalMlWorkerEntrypointPort }}</code>. Make sure that
                    it's accessible on the Giskard server machine.
                </p>
            </v-alert>
            <div>
                <p>To connect a worker, install giskard library in any code environment of your choice with</p>
                <CodeSnippet codeContent='pip install "giskard>=2.0.0b" -U' />
                <p class="mt-4 mb-4">then run</p>
                <CodeSnippet :codeContent="codeContent" />
                <p class="mt-4 mb-0">to connect to this Giskard server.</p>
                <div v-if="apiAccessToken && apiAccessToken.id_token">
                    <p>Finally, use the following API Access Token to connect:</p>
                    <CodeSnippet :codeContent="apiAccessToken.id_token" :language="'bash'"></CodeSnippet>
                </div>
                <p class="mt-4" v-if="route.name !== 'admin-general'">You can check the status of an ML Worker and generate a new API token on the
                    <router-link :to="{ name: 'admin-general' }">Settings</router-link>
                    page
                </p>
            </div>
            <v-card-actions>
                <div class="d-flex align-center">
                    <v-btn color="primary" @click="checkForExternalWorker">Reload</v-btn>
                </div>
            </v-card-actions>
        </v-card-text>
    </v-card>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useMainStore } from "@/stores/main";
import { useMLWorkerStore } from "@/stores/ml-worker";
import { useRoute } from "vue-router/composables";
import { apiURL } from "@/env";
import { JWTToken } from "@/generated-sources";
import CodeSnippet from "./CodeSnippet.vue";
import { api } from "@/api";
import { TYPE } from "vue-toastification";

const appSettings = computed(() => mainStore.appSettings);

const mainStore = useMainStore();
const mlWorkerStore = useMLWorkerStore();
const route = useRoute();


const apiAccessToken = ref<JWTToken | null>(null);

const codeContent = computed(() => {
    return `giskard worker start -u ${apiURL}`;
})

const generateApiAccessToken = async () => {
    try {
        apiAccessToken.value = await api.getApiAccessToken();
    } catch (error) {
        console.log(error);
    }
}

async function checkForExternalWorker() {
    await mlWorkerStore.checkExternalWorkerConnection();
    if (mlWorkerStore.isExternalWorkerConnected) {
        useMainStore().addNotification({
            content: 'External ML Worker is connected!',
            color: TYPE.SUCCESS,
        });
    } else {
        useMainStore().addNotification({
            content: 'External ML Worker is not connected',
            color: TYPE.ERROR,
        });
    }
}

onMounted(async () => {
    await generateApiAccessToken();
})
</script>
