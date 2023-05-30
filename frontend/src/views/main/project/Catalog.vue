<template>
    <div class="vc mt-2 pb-0" v-if="catalog">
        <div>
            <v-btn text outlined color="primary" class="ma-1 rounded-pill tab" :to="{ name: 'project-catalog-datasets' }">
                <v-icon left small class="mr-1">mdi-database</v-icon>
                Datasets
            </v-btn>
            <v-btn text outlined class="ma-1 rounded-pill tab" :to="{ name: 'project-catalog-models' }" color="primary">
                <v-icon left small class="mr-1">mdi-cube-outline</v-icon>
                Models
            </v-btn>
            <v-btn text outlined class="ma-1 rounded-pill tab" :to="{ name: 'project-catalog-tests' }" color="primary">
                <v-icon left small class="mr-1">mdi-test-tube</v-icon>
                Tests
            </v-btn>
            <v-btn text outlined class="ma-1 rounded-pill tab" :to="{ name: 'project-catalog-slicing-functions' }" color="primary">
                <v-icon left small class="mr-1">mdi-knife</v-icon>
                Slicing functions
            </v-btn>
            <v-btn text outlined class="ma-1 rounded-pill tab" :to="{ name: 'project-catalog-transformation-functions' }" color="primary">
                <v-icon left small class="mr-1">mdi-chart-bell-curve</v-icon>
                Transformation functions
            </v-btn>
        </div>
        <router-view />
    </div>
    <LoadingFullscreen v-else name="catalog" />
</template>

<script setup lang="ts">
import {onActivated, onDeactivated, ref} from "vue";
import {useCatalogStore} from "@/stores/catalog";
import {storeToRefs} from "pinia";
import LoadingFullscreen from "@/components/LoadingFullscreen.vue";
import { useRouter, useRoute } from "vue-router/composables";
import {schedulePeriodicJob} from "@/utils/job-utils";

const router = useRouter();
const route = useRoute();

let props = defineProps<{
    projectId: number,
    suiteId?: number
}>();

const catalogStore = useCatalogStore();
const { catalog } = storeToRefs(catalogStore);

const defaultRoute = 'project-catalog-datasets';

const refreshingRef = ref<() => void>();

onActivated(async () => {
    refreshingRef.value = schedulePeriodicJob(async () => await catalogStore.loadCatalog(props.projectId), 1000)
    await catalogStore.loadCatalog(props.projectId)
    if (route.name === 'project-catalog') {
        await router.push({ name: defaultRoute });
    }
});

onDeactivated(() => {
    console.log('onUnmounted')
    refreshingRef.value!()
})
</script>

<style scoped>
.tab {
    text-transform: none !important;
}

.v-btn--active.tab {
    border-color: #087038 !important;
}
</style>
