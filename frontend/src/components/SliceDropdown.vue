<template>
  <v-autocomplete label="Slice to apply"
                  :items="items"
                  v-model="slice"
                  placeholder="Select a slice..."
                  :loading="loading"
                  clearable></v-autocomplete>
</template>

<script setup lang="ts">
import {computed, onMounted, ref, watch} from "vue";
import {SliceDTO} from "@/generated-sources";
import {api} from "@/api";

interface Props {
  projectId: number,
  loading?: boolean,
  create?: boolean
}

const props = defineProps<Props>();
const emit = defineEmits(["onSelect", "onClear"])

const slices = ref<SliceDTO[]>([])
const slice = ref<SliceDTO | null>(null);

onMounted(() => {
  loadSlices();
})

const items = computed(() => {
  return slices.value.map(slice => ({
    ...slice,
    text: slice.name,
    value: slice
  }));
})

watch(() => slice.value, (value) => {
  if (value !== null) {
    emit('onSelect', value);
  } else {
    emit('onClear');
  }
})

async function loadSlices() {
  slices.value = await api.getProjectSlices(props.projectId)
}
</script>

<style scoped>

</style>