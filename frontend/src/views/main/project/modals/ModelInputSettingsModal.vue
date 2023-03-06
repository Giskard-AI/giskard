<template>
  <vue-final-modal
      v-slot="{ close }"
      v-bind="$attrs"
      classes="modal-container"
      content-class="modal-content"
      v-on="$listeners"
  >
    <v-form @submit.prevent="">
      <ValidationObserver ref="observer" v-slot="{ invalid }">
        <v-card>
          <v-card-title>
            Edit {{ meta.suiteInputType }} settings
          </v-card-title>

          <v-card-text>
            <template v-for="{name, type} in availableMeta">
              <v-text-field
                  v-if="type === 'string'"
                  :label="name" v-model="meta[name]"/>

              <v-select
                  v-else-if="Array.isArray(type)"
                  :label="name" :items="type" v-model="meta[name]"/>
            </template>
          </v-card-text>

          <v-divider></v-divider>

          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn
                color="primary"
                text
                :disabled="invalid"
                @click="save(close)"
            >
              Save
            </v-btn>
          </v-card-actions>
        </v-card>
      </ValidationObserver>
    </v-form>
  </vue-final-modal>
</template>

<script setup lang="ts">

import {computed, onMounted, ref} from 'vue';
import {GenerateTestSuiteInputDTO} from '@/generated-sources';

const {input} = defineProps<{
  input: GenerateTestSuiteInputDTO
}>();

const meta = ref<any>({});
const emit = defineEmits(['save']);

onMounted(() => {
  meta.value = {
    ...input,
    suiteInputType: input.type.toLowerCase()
  }
})

const availableMeta = computed(() => {
  switch (meta.value.suiteInputType) {
    case 'model':
      return [{
        name: 'modelType',
        type: ['classification', 'regression']
      }];
    case 'dataset':
      return [{
        name: 'target',
        type: 'string'
      }];
    default:
      return []
  }
})


async function save(close) {
  emit('save', meta.value)
  close();
}

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

</style>
