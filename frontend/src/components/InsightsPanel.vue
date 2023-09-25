<template>
  <v-switch :loading="loading" :color="count > 0 ? 'warning' : ''" label="Insights" v-model="active"></v-switch>
</template>

<script setup lang="ts">
import {usePushStore} from "@/stores/push";
import {computed} from "vue";
import {storeToRefs} from "pinia";

const pushStore = usePushStore();


const {loading, active} = storeToRefs(pushStore);

const count = computed(() => {
  if (pushStore.current == undefined) {
    return 0;
  }
  return Object.values(pushStore.current).filter((push) => push).length;
});

</script>

<style scoped>

</style>