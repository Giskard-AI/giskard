<template>
  <v-btn-toggle v-model="selected">
    <v-btn :loading="loading" :color="count > 0 ? 'warning' : ''">{{ count }} insights</v-btn>
  </v-btn-toggle>
</template>

<script setup lang="ts">
import {usePushStore} from "@/stores/push";
import {computed, ref, watch} from "vue";
import {storeToRefs} from "pinia";

const pushStore = usePushStore();

const selected = ref<number>(0);

const {loading} = storeToRefs(pushStore);

watch(() => selected.value, (value) => {
  if (value == undefined) {
    pushStore.active = false;
  } else {
    pushStore.active = true;
  }
});

const count = computed(() => {
  if (pushStore.current == undefined) {
    return 0;
  }
  return Object.values(pushStore.current).filter((push) => push).length;
});

</script>

<style scoped>

</style>