<template>
  <div v-if="catalog" class="vc pb-0">
    <div>
      <v-btn :to="{ name: 'project-catalog-tests' }" class="ma-1 rounded-pill tab" color="primary" outlined text
             @click="trackTabChange('project-catalog-tests')">
        <v-icon class="mr-1" left small>mdi-test-tube</v-icon>
        Tests
      </v-btn>
      <v-btn :to="{ name: 'project-catalog-slicing-functions' }" class="ma-1 rounded-pill tab" color="primary" outlined
             text
             @click="trackTabChange('project-catalog-slicing-functions')">
        <v-icon class="mr-1" left small>mdi-knife</v-icon>
        Slicing functions
      </v-btn>
      <v-btn :to="{ name: 'project-catalog-transformation-functions' }" class="ma-1 rounded-pill tab" color="primary"
             outlined
             text
             @click="trackTabChange('project-catalog-transformation-functions')">
        <v-icon class="mr-1" left small>mdi-chart-bell-curve</v-icon>
        Transformation functions
      </v-btn>
      <v-btn :to="{ name: 'project-catalog-models' }" class="ma-1 rounded-pill tab" color="primary" outlined text
             @click="trackTabChange('project-catalog-datasets')">
        <v-icon class="mr-1" left small>mdi-cube-outline</v-icon>
        Models
      </v-btn>
      <v-btn :to="{ name: 'project-catalog-datasets' }" class="ma-1 rounded-pill tab" color="primary" outlined text
             @click="trackTabChange('project-catalog-datasets')">
        <v-icon class="mr-1" left small>mdi-database</v-icon>
        Datasets
      </v-btn>
    </div>
    <router-view/>
  </div>
  <LoadingFullscreen v-else name="catalog"/>
</template>

<script lang="ts" setup>
import {onActivated, onDeactivated, ref, watch} from "vue";
import {useCatalogStore} from "@/stores/catalog";
import {storeToRefs} from "pinia";
import {useRoute, useRouter} from "vue-router/composables";
import {schedulePeriodicJob} from "@/utils/job-utils";
import mixpanel from "mixpanel-browser";
import LoadingFullscreen from "@/components/LoadingFullscreen.vue";

const route = useRoute();
const router = useRouter();
const catalogStore = useCatalogStore();

let props = defineProps<{
  projectId: number,
  suiteId?: number
}>();

const componentRoute = 'project-catalog';
const defaultRoute = 'project-catalog-tests';

const {catalog} = storeToRefs(catalogStore);
const refreshingRef = ref<() => void>();


function trackTabChange(name: string) {
  mixpanel.track("Catalog tab change", {
    from: route.name,
    to: name
  });
}

async function checkAndRedirect() {
  if (route.name === componentRoute) {
    router.push({name: defaultRoute});
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

::v-deep .v-toolbar__content {
  padding-left: 4px !important;
  display: inline-flex;
  flex-direction: column;
}
</style>
