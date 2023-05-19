<template>
    <div class="vc mt-2 pb-0" v-if="catalog">
        <v-tabs>
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
        </v-tabs>
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
