<template>
  <v-container fluid class="vc">
    <v-row>
      <code>{{ props.projectId }}</code>
      <code>{{ props.suiteId }}</code>
      <v-col cols="2">
        <v-tabs vertical v-model="tab">
          <v-tab>Inputs & parameters</v-tab>
          <v-tab>Tests</v-tab>
          <v-tab>Configuration</v-tab>
          <v-tab>Execution</v-tab>
        </v-tabs>
      </v-col>
      <v-col>
        <v-tabs-items v-model="tab">
          <v-tab-item :transition="false">
            Inputs view
          </v-tab-item>
          <v-tab-item :transition="false" v-if="registry">
            <v-row>
              <SuiteTests></SuiteTests>
            </v-row>
          </v-tab-item>
        </v-tabs-items>
      </v-col>
    </v-row>
  </v-container>
</template>

<script lang="ts" setup>

import {api} from "@/api";
import {onMounted, ref} from "vue";
import {TestCatalogDTO, TestSuiteNewDTO} from "@/generated-sources";

const props = defineProps<{
  projectId: number,
  suiteId: number,
}>();

let suite = ref<TestSuiteNewDTO | null>(null);
let registry = ref<TestCatalogDTO | null>(null);
let tab = ref<any>(null);
onMounted(async () => {
  suite.value = await api.getTestSuiteNew(props.projectId, props.suiteId);
  registry.value = await api.getTestsCatalog(props.projectId);
})


</script>