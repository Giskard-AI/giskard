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
import { onActivated, onDeactivated, ref, watch } from "vue";
import { useCatalogStore } from "@/stores/catalog";
import { storeToRefs } from "pinia";
import LoadingFullscreen from "@/components/LoadingFullscreen.vue";
import { useRouter, useRoute } from "vue-router/composables";
import { schedulePeriodicJob } from "@/utils/job-utils";

const router = useRouter();
const route = useRoute();

let props = defineProps<{
    projectId: number,
    suiteId?: number
}>();

const catalogStore = useCatalogStore();
const { catalog } = storeToRefs(catalogStore);

const componentRoute = 'project-catalog';
const defaultRoute = 'project-catalog-tests';

const refreshingRef = ref<() => void>();

async function checkAndRedirect() {
    if (route.name === componentRoute) {
        router.push({ name: defaultRoute });
    }
}

watch(() => route.name, async (name) => {
    await checkAndRedirect();
})


onActivated(async () => {
    refreshingRef.value = schedulePeriodicJob(async () => await catalogStore.loadCatalog(props.projectId), 1000)
    await catalogStore.loadCatalog(props.projectId)
    await checkAndRedirect();
});

onDeactivated(() => {
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
