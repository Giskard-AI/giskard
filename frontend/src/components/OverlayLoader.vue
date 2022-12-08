<template>
  <v-overlay :value="show" :absolute="absolute"
             :color="solid ? '#ffffff':'#cdcdcd90'" :opacity="solid ? 1: 0.46"
             :class="classes"
             :z-index="100">
    <v-progress-circular class="ma-2" :size="size" color="primary" indeterminate></v-progress-circular>
  </v-overlay>
</template>

<script setup lang="ts">
import {computed} from "vue";

interface Props {
  size: number,
  solid: boolean,
  show: boolean,
  absolute: boolean,
  noFade: boolean
}

const props = withDefaults(defineProps<Props>(), {
  size: 50,
  noFade: false
});

const classes = computed(() => {
  return {
    'no-fade': props.noFade
  }
});
</script>

<style lang="scss">
.v-overlay {
  &.no-fade {
    transition-duration: 0s;
  }
}
</style>