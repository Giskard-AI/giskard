<template>
    <p>
        <!-- <v-range-slider
            v-model="range"
            :min="min_weight"
            :max="max_weight"
            label="Filter Lime Values"
        ></v-range-slider> -->
        <span v-for="(i, n) in props.words.length"
              class="word"
              :style="{ backgroundColor: calculateBackgroundColor(props.weights[n]) }"
              >{{props.words[n]}}</span>
    </p>
</template>


<script setup lang="ts">
import { onMounted, ref } from 'vue';


const props = defineProps<{
    weights: number[]
    words: string[]
    max_weight: number
    min_weight: number
}>();

// const range = ref<number[]>([0, 0])

const absolute_max_weight = ref<number>(0)

onMounted(() => {
    absolute_max_weight.value = Math.max(Math.abs(props.max_weight), Math.max(props.min_weight));
})

function calculateBackgroundColor(weight: number){
    if (weight === 0){
        return 'transparent';
    }
    else {
        let color = (weight > 0) ? 'rgba(0, 240, 0, ' : 'rgba(256, 0, 0, ';
        color += Math.abs(weight) / absolute_max_weight.value + ')'; 
        return color
    }
}


</script>

<style>
    .word {
        border-radius: 5px;
        padding-left: 3px;
        padding-right: 3px;
    }
</style>