<template>
  <svg :height="svgSize" :width="svgSize">
    <rect
        v-for="square in squares"
        :x="square.x"
        :y="square.y"
        :width="square.size"
        :height="square.size"
        :style="square.style"
    />
  </svg>
</template>

<script setup lang="ts">

import {computed} from 'vue';

const {results} = defineProps<{ results: boolean[] }>();

const svgSize = 32;
const paddingRatio = 5 / 100;

const squares = computed(() => {
  const itemPerRow = Math.ceil(Math.sqrt(results.length));
  const size = svgSize / itemPerRow;
  const padding = size * paddingRatio;
  const sizeWithPadding = size - 2 * padding;

  return results.map((result, i) => ({
    x: (i % itemPerRow) * size + padding,
    y: Math.floor(i / itemPerRow) * size + padding,
    size: sizeWithPadding,
    style: `fill:${result ? '#4caf50' : '#f44336'}`
  }));
});

</script>
