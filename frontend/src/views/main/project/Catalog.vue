<template>
    <div class="vc mt-2 pb-0" v-if="catalog">
        <v-tabs>
            <v-tab :to="{name: 'project-catalog-tests'}">
                Tests
            </v-tab>
            <v-tab :to="{name: 'project-catalog-slicing-functions'}">
                Slicing functions
            </v-tab>
            <v-tab :to="{name: 'project-catalog-transformation-functions'}">
                Transformation functions
            </v-tab>
        </v-tabs>
        <router-view/>
    </div>
    <LoadingFullscreen v-else name="catalog"/>
</template>

<script setup lang="ts">
import {onActivated, onDeactivated, ref} from "vue";
import {useCatalogStore} from "@/stores/catalog";
import {storeToRefs} from "pinia";
import LoadingFullscreen from "@/components/LoadingFullscreen.vue";
import {schedulePeriodicJob} from "@/utils/job-utils";

let props = defineProps<{
    projectId: number,
    suiteId?: number
}>();

const catalogStore = useCatalogStore();
const {catalog} = storeToRefs(catalogStore);

const refreshingRef = ref<() => void>();

onActivated(() => refreshingRef.value = schedulePeriodicJob(async () => await catalogStore.loadCatalog(props.projectId), 1000));

onDeactivated(() => {

    console.log('onUnmounted')
    refreshingRef.value!()
})

</script>
