<template>
  <div class="d-flex">
    <div v-show="!editable">{{ label }}</div>
    <v-text-field v-show="editable" v-model="label"></v-text-field>
    <v-icon class="mode-switch" @click="editable = !editable">edit</v-icon>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

interface Props {
  label?: string;
}

const props = defineProps<Props>();

const editable = ref(false);
</script>

<style scoped lang="scss">
@import "src/styles/colors";

.mode-switch {
  &:hover {
    cursor: pointer;
    color: $color-giskard-main;
  }
}
</style>