<template>
  <div class="vc mt-2 pb-0">
    <div class="vc">
      <v-container class="main-container vc">
        <v-row>
          <v-col :align="'right'">
            <div class="d-flex">
              <v-btn v-if="route.name === 'test-suite-overview'" text :to="{ name: 'test-suite-executions' }" color="secondary">
                <v-icon left>history</v-icon>
                Past executions
              </v-btn>
              <v-btn v-else text :to="{ name: 'test-suite-overview' }" color="secondary">
                <v-icon>arrow_left</v-icon>
                Overview
              </v-btn>
              <div class="flex-grow-1" />
              <v-btn tile class='mx-1' v-if="hasTest" :to="{ name: 'project-catalog-tests', query: { suiteId: suiteId } }" color="secondary">
                <v-icon>add</v-icon>
                Add test
              </v-btn>
              <v-btn tile class='mx-1' v-if="hasTest" @click='openRunTestSuite(true)' color="secondary">
                <v-icon>compare</v-icon>
                Compare
              </v-btn>
              <v-btn tile class='mx-1' v-if="hasTest" @click='() => openRunTestSuite(false)' color="primary">
                <v-icon>arrow_right</v-icon>
                Run test suite
              </v-btn>
            </div>
          </v-col>
        </v-row>
        <v-row class="vc">
          <v-col class="vc" cols="12">
            <router-view />
          </v-col>
        </v-row>
      </v-container>
    </div>
  </div>
</template>

<script lang="ts" setup>

import { onActivated, watch } from "vue";
import { useMainStore } from "@/stores/main";
import { useTestSuiteStore } from '@/stores/test-suite';
import { storeToRefs } from 'pinia';
import { useRoute, useRouter } from 'vue-router/composables';
import { $vfm } from 'vue-final-modal';
import RunTestSuiteModal from '@/views/main/project/modals/RunTestSuiteModal.vue';
import { useCatalogStore } from "@/stores/catalog";

const props = defineProps<{
  projectId: number,
  suiteId: number
}>();

const mainStore = useMainStore();
const { inputs, executions } = storeToRefs(useTestSuiteStore())

onActivated(() => loadData());
watch(() => props.suiteId, () => loadData());

const { loadTestSuites } = useTestSuiteStore();
const { loadCatalog } = useCatalogStore();

const router = useRouter();
const route = useRoute();

async function loadData() {
  await loadTestSuites(props.projectId, props.suiteId);
  await loadCatalog(props.projectId);
}

async function openRunTestSuite(compareMode: boolean) {
  await $vfm.show({
    component: RunTestSuiteModal,
    bind: {
      projectId: props.projectId,
      suiteId: props.suiteId,
      inputs: inputs.value,
      compareMode,
      previousParams: executions.value.length === 0 ? {} : executions.value[0].inputs
    }
  });
}

const { hasTest } = storeToRefs(useTestSuiteStore());

</script>


<style scoped lang="scss">
.main-container {
  width: 100%;
  max-width: 100%;
}
</style>
