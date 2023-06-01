<template>

  <v-tooltip bottom>
    <template v-slot:activator="{ on}">
      <svg :height="svgSize" :width="svgSize" v-on="on">
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
    <span>{{ results.filter(r => r).length }} /  {{ results.length }}</span>
  </v-tooltip>
</template>

<script setup lang="ts">

import {computed} from 'vue';
import {Colors} from '@/utils/colors';

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
    style: `fill:${result ? Colors.PASS : Colors.FAIL}`
  }));
});

</script>
