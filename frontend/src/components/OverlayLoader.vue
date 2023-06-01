<template>
  <v-overlay :value="show" :absolute="absolute"
             :color="solid ? '#ffffff':'#cdcdcd90'" :opacity="solid ? 1: 0.46"
             :class="classes"
             :z-index="100">
    Vue.component("v-chart", ECharts);
  </v-overlay>
</template>

<script setup lang="ts">
import {computed} from "vue";

interface Props {
  show: boolean,
  size?: number,
  solid?: boolean,
  absolute?: boolean,
  noFade?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  size: 50,
  solid: false,
  noFade: false,
  absolute: false
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
