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
        <!-- <v-tabs>
            <v-tab :to="{ name: 'project-catalog-datasets' }">
                Datasets
            </v-tab>
            <v-tab :to="{ name: 'project-catalog-models' }">
                Models
            </v-tab>
            <v-tab :to="{ name: 'project-catalog-tests' }">
                Tests
            </v-tab>
            <v-tab :to="{ name: 'project-catalog-slicing-functions' }">
                Slicing functions
            </v-tab>
            <v-tab :to="{ name: 'project-catalog-transformation-functions' }">
                Transformation functions
            </v-tab>
        </v-tabs> -->
        <router-view />
    </div>
    <LoadingFullscreen v-else name="catalog" />
</template>

<script setup lang="ts">
import { onActivated } from "vue";
import { useCatalogStore } from "@/stores/catalog";
import { storeToRefs } from "pinia";
import LoadingFullscreen from "@/components/LoadingFullscreen.vue";
import { useRouter } from "vue-router/composables";

const router = useRouter();

let props = defineProps<{
    projectId: number,
    suiteId?: number
}>();

const catalogStore = useCatalogStore();
const { catalog } = storeToRefs(catalogStore);

const defaultRoute = 'project-catalog-datasets';

onActivated(async () => {
    await catalogStore.loadCatalog(props.projectId)
    await router.push({ name: defaultRoute });
});
</script>

<style scoped>
.tab {
    text-transform: none !important;
}

.v-btn--active.tab {
    border-color: #087038 !important;
}
</style>
