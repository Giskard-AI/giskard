<template>
  <div class="vc mt-2 pb-0">
    <div class="vc">
      <v-container class="main-container vc">
        <v-row>
          <v-col :align="'right'">
            <div class="d-flex">
              <v-btn text @click="loadData()" color="secondary">Refresh
                <v-icon right>refresh</v-icon>
              </v-btn>
              <v-btn v-if="route.name === 'test-suite-overview'"
                     text :to="{name:'test-suite-executions'}" color="secondary">
                <v-icon>history</v-icon>
                Past executions
              </v-btn>
              <v-btn v-else
                     text :to="{name:'test-suite-overview'}" color="secondary">
                <v-icon>arrow_left</v-icon>
                Overview
              </v-btn>
              <div class="flex-grow-1"/>
              <v-btn tile class='mx-1'
                     v-if="Object.entries(inputs).length > 0"
                     @click='() => openRunTestSuite(true)'
                     color="secondary">
                <v-icon>compare</v-icon>
                Compare
              </v-btn>
              <v-btn tile class='mx-1'
                     @click='() => openRunTestSuite(false)'
                     color="primary">
                <v-icon>arrow_right</v-icon>
                Run test suite
              </v-btn>
            </div>
          </v-col>
        </v-row>
        <v-row class="vc">
          <v-col class="vc" cols="12">
            <router-view/>
          </v-col>
        </v-row>
      </v-container>
    </div>
  </div>
</template>

<script lang="ts" setup>

import {onMounted, watch} from "vue";
import {useMainStore} from "@/stores/main";
import {useTestSuiteStore} from '@/stores/test-suite';
import {storeToRefs} from 'pinia';
import {useRoute} from 'vue-router/composables';
import {$vfm} from 'vue-final-modal';
import RunTestSuiteModal from '@/views/main/project/modals/RunTestSuiteModal.vue';

const props = defineProps<{
  projectId: number,
  suiteId: number
}>();

const mainStore = useMainStore();
const {inputs, executions} = storeToRefs(useTestSuiteStore())

onMounted(() => loadData());
watch(() => props.suiteId, () => loadData());

const {loadTestSuite} = useTestSuiteStore();

const route = useRoute();

async function loadData() {
  await loadTestSuite(props.projectId, props.suiteId);
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
</script>


<style scoped lang="scss">
.main-container {
  width: 100%;
  max-width: 100%;
}
</style>
