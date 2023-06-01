<template>
  <v-container fluid class="vc">
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
    <v-row>
      <v-col cols="2">
        <v-tabs vertical>
          <v-tab :to="{name:'test-suite-new-inputs'}">Inputs & parameters</v-tab>
          <v-tab :to="{name:'test-suite-new-tests'}">Tests</v-tab>
          <v-tab :to="{name:'test-suite-new-configuration'}">Configuration</v-tab>
          <v-tab :to="{name:'test-suite-new-execution'}">Execution</v-tab>
        </v-tabs>
      </v-col>
      <v-col cols="10">
        <router-view/>
      </v-col>
    </v-row>
  </v-container>
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
