<template>
  <vue-final-modal v-slot="{ close }" v-bind="$attrs" classes="modal-container" content-class="modal-content" v-on="$listeners">
    <div class="text-center">
      <v-card class="modal-card">
        <v-card-title>
          Create new slicing function
        </v-card-title>
        <v-card-text>
          <v-row v-if="false">
            <v-col>
              <p class="text-subtitle-1 text-left mb-0">Select the scope</p>
              <v-radio-group v-model="scope" class="mt-0" row>
                <v-radio label="Specific dataset" value="dataset"></v-radio>

                <v-tooltip bottom>
                  <template v-slot:activator="{ on, attrs }">
                    <div v-on="on">
                      <v-radio label="General" value="general" disabled></v-radio>
                    </div>
                  </template>
                  <span>Coming soon</span>
                </v-tooltip>
              </v-radio-group>
            </v-col>
          </v-row>
          <v-row v-if="scope === 'dataset'">
            <v-col>
              <p class="text-subtitle-1 text-left mb-1">Select a dataset</p>
              <DatasetSelector :projectId="projectId" :value.sync="selectedDataset" :return-object="true" label="Dataset" class="selector mb-4">
              </DatasetSelector>
            </v-col>
          </v-row>
          <v-row v-if="scope === 'dataset' && selectedDataset !== null">
            <v-col>
              <p class="text-subtitle-1 text-left mb-1">Define slice parameters</p>
              <ColumnFilterCreator v-for="(columnFilter, idx) in columnFilters" :key="idx" :dataset="selectedDataset" :column-name.sync="columnFilter.columnName" :column-type.sync="columnFilter.columnType" :slicing-type.sync="columnFilter.comparisonType" :value.sync="columnFilter.value" />
            </v-col>
          </v-row>

        </v-card-text>
        <v-card-actions>
          <div class="flex-grow-1"></div>
          <v-btn text @click="close">Cancel</v-btn>
          <v-btn color="primary" @click="create(close)" :disabled="isButtonDisabled">
            Create</v-btn>
        </v-card-actions>
      </v-card>
    </div>
  </vue-final-modal>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { DatasetDTO, ColumnType, ComparisonClauseDTO } from '@/generated-sources';
import DatasetSelector from '@/views/main/utils/DatasetSelector.vue';
import ColumnFilterCreator from "@/views/main/utils/ColumnFilterCreator.vue";
import { useCatalogStore } from "@/stores/catalog";


interface Props {
  projectId: number;
}

const props = defineProps<Props>();

const columnFilters = ref<Array<Partial<ComparisonClauseDTO & { columnType: ColumnType }>>>([{}]);


const scope = ref<string>('dataset');
const selectedDataset = ref<DatasetDTO | null>(null);

const isButtonDisabled = computed(() => {
  if (scope.value === 'dataset') {
    return selectedDataset.value === null || columnFilters.value.length === 0 || columnFilters.value.some(f => f.columnName === undefined || f.columnType === undefined || f.comparisonType === undefined)
  }
})


const emit = defineEmits(['created']);

async function create(close) {
  if (selectedDataset.value === null) {
    return
  }
  const slicingFunction = await useCatalogStore().createSlicingFunction(selectedDataset.value, columnFilters.value)
  emit('created', slicingFunction.uuid);
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
}

.modal-card {
  min-width: 50vw;
  max-height: 80vh;
  overflow-y: auto;
}
</style>
