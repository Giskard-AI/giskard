<template>
  <v-container>
    <div>TESTS</div>
    <div>{{ props }}</div>
  </v-container>
</template>

<script lang="ts" setup>

const props = defineProps<{
  projectId: number,
  suiteId: number,
}>();


</script>