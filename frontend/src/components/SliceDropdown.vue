<template>
  <v-autocomplete label="Slice to apply" :items="items" v-model="slice" placeholder="Select a slice..." clearable></v-autocomplete>
</template>

<script setup lang="ts">
import {computed, onMounted, ref, watch} from "vue";
import {SliceDTO} from "@/generated-sources";
import {api} from "@/api";

interface Props {
  projectId: number
}

const props = defineProps<Props>();
const emit = defineEmits(["onSelect"])

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
  emit('onSelect', value);
})

async function loadSlices() {
  slices.value = await api.getProjectSlices(props.projectId)
}

// TODO: Emit an on select slice event that can tell the parent we selected a slice and what to do with it ?

</script>

<style scoped>

</style>