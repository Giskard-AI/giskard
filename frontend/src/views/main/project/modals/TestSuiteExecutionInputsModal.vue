<template>
  <vue-final-modal
      v-slot="{ close }"
      v-bind="$attrs"
      classes="modal-container"
      content-class="modal-content"
      v-on="$listeners"
  >
    <div class="text-center">
      <v-card>
        <v-card-title>
          <p class="text-h6">Global inputs</p>
        </v-card-title>
        <v-card-text class="card-content">
          <TestInputList :models="models" :inputs="execution.inputs"
                         :input-types="inputs" :datasets="datasets"/>
        </v-card-text>
        <v-card-actions>

        </v-card-actions>
      </v-card>
    </div>
  </vue-final-modal>
</template>

<script setup lang="ts">

import {TestSuiteExecutionDTO} from '@/generated-sources';
import {ref} from 'vue';
import {storeToRefs} from 'pinia';
import {useTestSuiteStore} from '@/stores/test-suite';
import TestInputList from '@/components/TestInputList.vue';

const {execution} = defineProps<{
  execution: TestSuiteExecutionDTO
}>();

const {models, datasets, inputs} = storeToRefs(useTestSuiteStore());

const editor = ref(null)

</script>

<style scoped>
::v-deep(.modal-container) {
  display: flex;
  justify-content: center;
  align-items: center;
}

::v-deep(.modal-content) {
  position: relative;
  display: flex;
  flex-direction: column;
  margin: 0 1rem;
  padding: 1rem;
  min-width: 50vw;
}

.card-content {
  text-align: start;
}

</style>
