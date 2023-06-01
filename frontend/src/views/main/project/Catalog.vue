<template>
    <div class="vc mt-2 pb-0" v-if="catalog">
        <v-tabs>
            <v-tab :to="{name: 'project-catalog-test'}">
                Tests
            </v-tab>
        </v-tabs>
        <router-view/>
    </div>
    <v-container fill-height v-else>
        <v-layout align-center justify-center>
            <v-flex>
                <div class="text-center">
                    <div class="headline my-5">Loading catalog...</div>
                    <v-progress-circular
                        size="100"
                        indeterminate
                        color="primary"
                    ></v-progress-circular>
                </div>
            </v-flex>
        </v-layout>
    </v-container>
</template>

<script setup lang="ts">
import {onActivated} from "vue";
import {useCatalogStore} from "@/stores/catalog";
import {storeToRefs} from "pinia";

let props = defineProps<{
    projectId: number,
    suiteId?: number
}>();

const catalogStore = useCatalogStore();
const {catalog} = storeToRefs(catalogStore);

onActivated(async () => await catalogStore.loadCatalog(props.projectId));

</script>
