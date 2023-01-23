<template>
  <svg height="32" width="32">
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

const squares = computed(() => {
  const itemPerRow = Math.ceil(Math.sqrt(results.length));
  const size = 32 / itemPerRow;
  const padding = size / 20;
  const sizeWithPadding = size - 2 * padding;

  return results.map((result, i) => ({
    x: (i % itemPerRow) * size + padding,
    y: Math.floor(i / itemPerRow) * size + padding,
    size: sizeWithPadding,
    style: `fill:${result ? '#4caf50' : '#f44336'}`
  }));
});

</script>
