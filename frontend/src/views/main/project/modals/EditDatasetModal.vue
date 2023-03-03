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
          Edit dataset "{{ dataset.name ?? dataset.id }}"
        </v-card-title>
        <v-card-text class="modal-body">
          <v-expansion-panels>
            <v-expansion-panel v-for="feature in Object.keys(businessNames)" :key="feature">

              <v-expansion-panel-header>
                {{ feature }}
              </v-expansion-panel-header>
              <v-expansion-panel-content>
                <v-text-field v-model="businessNames[feature]"
                              label="Business name" dense
                              outlined></v-text-field>
                <div v-if="categoryBusinessNames.hasOwnProperty(feature)">
                  <p class="text-h6">Category business names</p>
                  <v-text-field v-for="category in Object.keys(categoryBusinessNames[feature])"
                                v-model="categoryBusinessNames[feature][category]"
                                :label="category" dense outlined></v-text-field>
                </div>
              </v-expansion-panel-content>
            </v-expansion-panel>
          </v-expansion-panels>
        </v-card-text>
        <v-card-actions>
          <v-btn color="secondary" @click="close">Cancel</v-btn>
          <v-btn color="primary" @click="save(close)">Save</v-btn>
        </v-card-actions>
      </v-card>
    </div>
  </vue-final-modal>
</template>

<script setup lang="ts">


import {DatasetDTO, FeatureMetadataDTO, FeatureType} from '@/generated-sources';
import {onMounted, ref} from 'vue';
import {chain} from 'lodash';
import {api} from '@/api';

const {dataset} = defineProps<{
  dataset: DatasetDTO
}>();

const featuresMetadata = ref<FeatureMetadataDTO[] | null>(null);
const businessNames = ref({});
const categoryBusinessNames = ref({});

const emit = defineEmits(['saved'])

onMounted(async () => {
  featuresMetadata.value = await api.getFeaturesMetadata(dataset.id);

  businessNames.value = chain(featuresMetadata.value)
      .keyBy('name')
      .mapValues((feature) => dataset.businessNames?.[feature.name] ?? '')
      .value();

  categoryBusinessNames.value = chain(featuresMetadata.value)
      .filter((feature) => feature.type === FeatureType.CATEGORY)
      .keyBy('name')
      .mapValues((feature) => chain(feature.values)
          .mapKeys(category => category)
          .mapValues(category => dataset.categoryBusinessNames?.[feature.name]?.[category] ?? '')
          .value()
      ).value();
});


async function save(close) {
  const saved = await api.updateDataset({
    ...dataset,
    businessNames: businessNames.value,
    categoryBusinessNames: categoryBusinessNames.value
  });

  emit('saved', saved);

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
  min-width: 40vw;
  position: relative;
  display: flex;
  flex-direction: column;
  margin: 0 1rem;
  padding: 1rem;
}


.modal-body {
  max-height: 60vh;
  overflow-y: auto;
  margin: 4px;
}
</style>
