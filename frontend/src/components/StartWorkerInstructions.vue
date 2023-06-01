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
                <CodeSnippet :codeContent="'pip install giskard'" />
                <p class="mt-4 mb-4">then run</p>
                <CodeSnippet :codeContent="codeContent" />
                <p class="mt-4 mb-0">to connect to this Giskard server.</p>
                <p v-if="route.name !== 'admin-general'">You can check the status of an ML Worker and generate a new API token on the
                    <router-link :to="{ name: 'admin-general' }">Settings</router-link>
                    page
                </p>
            </div>
        </v-card-text>
    </v-card>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useMainStore } from "@/stores/main";
import { useRoute } from "vue-router/composables";
import { apiURL } from "@/env";
import { MLWorkerType } from "@/generated-sources";
import CodeSnippet from "./CodeSnippet.vue";

const appSettings = computed(() => mainStore.appSettings);

const mainStore = useMainStore();
const route = useRoute();

interface Props {
    mlWorkerType: MLWorkerType;
}

const props = withDefaults(defineProps<Props>(), {
    mlWorkerType: MLWorkerType.EXTERNAL
});

const isExternalWorker = computed(() => props.mlWorkerType === MLWorkerType.EXTERNAL);

const codeContent = computed(() => {
    if (isExternalWorker.value) {
        return `giskard worker start -u ${apiURL}`;
    } else {
        return `giskard worker start -s -u ${apiURL} # for internal worker`;
    }
})
</script>
