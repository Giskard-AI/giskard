<template>
    <v-card outlined v-if="needFetchWithHFAccessToken === false">
        <v-card-text>
            <v-alert class="pa-0 text-body-2" colored-border type="info">
                <p class="mb-0">ML Worker is a python process that allows Giskard to execute models in a user's
                    environment</p>
                <p v-if="appSettings">A worker communicates with the backend through WebSocket. Make sure that
                    your worker machine can access the Giskard server machine.
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
        </v-card-text>
    </v-card>
    <HuggingFaceTokenCard v-else-if="needFetchWithHFAccessToken" @submit="fetchAndSaveHFSpacesTokenWithAccessToken"/>
    <LoadingFullscreen v-else :name="'MLWorker instructions'"/>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useMainStore } from "@/stores/main";
import { useRoute } from "vue-router/composables";
import { apiURL } from "@/env";
import { JWTToken } from "@/generated-sources";
import CodeSnippet from "./CodeSnippet.vue";
import { api } from "@/api";
import { saveLocalHFToken, getLocalHFToken } from "@/utils";
import { fetchHFSpacesToken } from "@/snippets";
import HuggingFaceTokenCard from "./HuggingFaceTokenCard.vue";
import LoadingFullscreen from "./LoadingFullscreen.vue";
import {TYPE} from 'vue-toastification';

const appSettings = computed(() => mainStore.appSettings);

const mainStore = useMainStore();
const route = useRoute();


const apiAccessToken = ref<JWTToken | null>(null);
const needFetchWithHFAccessToken = ref<boolean | null>(null);

const generateMLWorkerConnectionInstruction = (hfspaceToken=null) => {
    if (mainStore.appSettings!.isRunningOnHfSpaces && hfspaceToken) {
        try {
            return `giskard worker start -u ${apiURL} -t ${hfspaceToken}`;
        } catch (error) {
            console.error(error);
        }
    }
    return `giskard worker start -u ${apiURL}`;
}

const codeContent = ref<string>(generateMLWorkerConnectionInstruction());

const generateApiAccessToken = async () => {
    try {
        apiAccessToken.value = await api.getApiAccessToken();
    } catch (error) {
        console.log(error);
    }
}

async function fetchAndSaveHFSpacesTokenWithAccessToken(accessToken: string) {
    if (mainStore.appSettings!.isRunningOnHfSpaces) {
        saveLocalHFToken(accessToken);
        const token = await fetchHFSpacesToken();
        if (token) {
            needFetchWithHFAccessToken.value = false;
            codeContent.value = generateMLWorkerConnectionInstruction(token);
        } else {
            needFetchWithHFAccessToken.value = true;
            mainStore.addNotification({content: 'Invalid Hugging Face access token', color: TYPE.ERROR});
        }
    }
}

async function attemptFetchHFSpacesToken() {
    const token = await fetchHFSpacesToken();
    if (token) {
        if (getLocalHFToken()) {
            codeContent.value = generateMLWorkerConnectionInstruction(token);
        }
        needFetchWithHFAccessToken.value = false;
    } else {
        // Access Token seems invalidated or private
        needFetchWithHFAccessToken.value = true;
    }
}

onMounted(async () => {
    await generateApiAccessToken();
    if (mainStore.appSettings!.isRunningOnHfSpaces) {
        await attemptFetchHFSpacesToken();
    }
})
</script>
