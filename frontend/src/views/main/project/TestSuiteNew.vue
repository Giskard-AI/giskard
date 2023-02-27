<template>
  <div class="vc mt-2 pb-0">
    <div class="vc">
      <v-container class="main-container vc">
        <v-row>
          <v-col :align="'right'">
            <div class="d-flex flex-row-reverse">
              <RunTestSuiteModal :inputs="inputs" :suite-id="suiteId" :project-id="projectId"/>
              <v-btn text @click="loadData()" color="secondary">Reload
                <v-icon right>refresh</v-icon>
              </v-btn>
            </div>
          </v-col>
        </v-row>
        <v-row class="vc">
          <v-col cols="2">
            <v-tabs vertical>
              <v-tab :to="{name:'test-suite-new-inputs'}">Inputs & parameters</v-tab>
              <v-tab :to="{name:'test-suite-new-tests'}">Tests</v-tab>
              <v-tab :to="{name:'test-suite-new-configuration'}">Configuration</v-tab>
              <v-tab :to="{name:'test-suite-new-executions'}">Execution</v-tab>
            </v-tabs>
          </v-col>
          <v-col cols="10" class="vc">
            <router-view/>
          </v-col>
        </v-row>
      </v-container>
    </div>
  </div>
</template>

<script lang="ts" setup>

import {onMounted, watch} from "vue";
import RunTestSuiteModal from '@/views/main/project/modals/RunTestSuiteModal.vue';
import {useMainStore} from "@/stores/main";
import {useTestSuiteStore} from '@/stores/test-suite';
import {storeToRefs} from 'pinia';

const props = defineProps<{
  projectId: number,
  suiteId: number
}>();

const mainStore = useMainStore();
const {inputs} = storeToRefs(useTestSuiteStore())

onMounted(() => loadData());
watch(() => props.suiteId, () => loadData());

const {loadTestSuite} = useTestSuiteStore();

async function loadData() {
  await loadTestSuite(props.projectId, props.suiteId);
}
</script>


<style scoped lang="scss">
.main-container {
  width: 100%;
  max-width: 100%;
}
</style>
