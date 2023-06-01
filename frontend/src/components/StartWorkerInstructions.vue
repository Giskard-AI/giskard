<template>
    <v-card outlined>
        <v-card-text>

            <v-alert class="pa-0 text-body-2" colored-border type="info" icon >
                <p class="mb-0">ML Worker is a python process that allows Giskard to execute models in a user's
                    environment</p>
                <p v-if="appSettings">A worker communicates with the backend through TCP port <code
                    class="font-weight-bold">{{ appSettings.externalMlWorkerEntrypointPort }}</code>. Make sure that
                    it's accessible on the Giskard server machine.
                </p>
            </v-alert>
            <p>To connect a worker, install giskard library in any code environment of your choice with</p>
            <p class="text-center"><code class="text-body-1">pip install giskard</code></p>
            <p>then run</p>
            <p class="text-center">

                <code class="text-body-1">
                    giskard worker start -u {{ apiURL }}
                </code>
                <v-btn class="ml-1" x-small icon @click="copyMLWorkerCommand">
                    <v-icon>mdi-content-copy</v-icon>
                </v-btn>
            </p>
            <p class="mt-4 mb-0">to connect to this Giskard server.</p>
            <p v-if="route.name !== 'admin-general'">You can check the status of an ML Worker in on the
                <router-link :to="{ name: 'admin-general' }">Settings</router-link>
                page
            </p>
        </v-card-text>
    </v-card>
</template>

<script setup lang="ts">
import {computed} from "vue";
import {useMainStore} from "@/stores/main";
import {copyToClipboard} from "@/global-keys";
import {useRoute} from "vue-router/composables";
import {apiURL} from "@/env";
import {TYPE} from "vue-toastification";

const appSettings = computed(() => mainStore.appSettings);

const mainStore = useMainStore();
const route = useRoute();

async function copyMLWorkerCommand() {
    await copyToClipboard(`giskard worker start -u ${apiURL}`);
    mainStore.addNotification({content: 'Copied', color: TYPE.INFO});
}
</script>
