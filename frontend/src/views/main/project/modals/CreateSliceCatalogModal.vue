<template>
  <vue-final-modal v-slot="{ close }" v-bind="$attrs" classes="modal-container" content-class="modal-content" v-on="$listeners">
    <div class="text-center">
      <v-card class="modal-card">
        <v-card-title>
          Create new slicing function
        </v-card-title>
        <v-card-text>
          <v-row>
            <v-col>
              <v-radio-group v-model="scope" row>
                <template v-slot:label>
                  <div>
                    <span class="text-h6 mr-6">Scope</span>
                  </div>
                </template>
                <v-radio label="Global" value="global"></v-radio>
                <v-radio label="Project" value="project"></v-radio>
                <v-radio label="Dataset" value="dataset"></v-radio>
              </v-radio-group>
            </v-col>
          </v-row>

        </v-card-text>
        <v-card-actions>
          <div class="flex-grow-1"></div>
          <v-btn text @click="close">Cancel</v-btn>
          <v-btn color="primary" @click="$emit('confirm', close)">Create</v-btn>
        </v-card-actions>
      </v-card>
    </div>
  </vue-final-modal>
</template>

<script setup lang="ts">
import { ref } from 'vue';

interface Props { }

const props = defineProps<Props>();

const scope = ref<string>('dataset');

const emit = defineEmits(['input']);
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
}

.modal-card {
  min-width: 50vw;
  max-height: 80vh;
  overflow-y: auto;
}
</style>
