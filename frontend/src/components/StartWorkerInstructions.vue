<template>
    <div>
        <p>To connect a worker, install giskard library in any code environment of your choice with</p>
        <p><code class="text-body-1">pip install giskard</code></p>
        <p>then run</p>
        <code class="text-body-1">
            giskard worker start -h
            <v-tooltip right>
                <template v-slot:activator="{ on, attrs }">
                          <span v-bind="attrs"
                                v-on="on" class="giskard-address">{{ giskardAddress }}</span>
                </template>
                <p>IP address, hostname or DNS name of Giskard server can be used.</p>
                <p>Make sure that port {{ appSettings.externalMlWorkerEntrypointPort }} is accessible</p>
            </v-tooltip>
            <span
                    v-if="appSettings.externalMlWorkerEntrypointPort !== 40051"> -p {{
                appSettings.externalMlWorkerEntrypointPort
                }}</span>
        </code>
        <v-btn class="ml-1" x-small icon @click="copyMLWorkerCommand">
            <v-icon>mdi-content-copy</v-icon>
        </v-btn>
        <p class="mt-4 mb-0">to connect to Giskard</p>
    </div>
</template>

<script setup lang="ts">
import {computed} from "vue";
import {useMainStore} from "@/stores/main";
import {copyToClipboard} from "@/global-keys";

const mainStore = useMainStore();

const appSettings = computed(() => mainStore.appSettings);
const giskardAddress = computed(() => window.location.hostname);

async function copyMLWorkerCommand() {
    await copyToClipboard('giskard worker start -h ' + giskardAddress.value);
    mainStore.addNotification({content: 'Copied', color: '#262a2d'});
}
</script>
