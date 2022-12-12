<template>
    <p>
        <span v-for="(n, index) in props.weights.length"
              :class="(Object.values(props.weights[index])[0] === 0) ? '' : 'impactWord'"
              :style="{ backgroundColor: calculateBackgroundColor(Object.values(props.weights[index])[0]) }"
              :key="n">{{Object.keys(props.weights[index])[0]}}</span>
    </p>
</template>


<script setup lang="ts">

const props = defineProps<{
    weights: { [key: string]: number }[]
    max_weight: number
}>();


function calculateBackgroundColor(weight: number){
    if (weight === 0){
        return 'transparent';
    }
    else {
        let color = (weight > 0) ? '#00FF00' : '#FF0000';
        weight = Math.abs(weight) * 240 / props.max_weight;
        color = (weight < 16) ? color + '0' : color;
        return color + weight.toString(16).split('.')[0];
    }
}


</script>

<style>
    .impactWord {
        border-radius: 5px;
        padding-left: 3px;
        padding-right: 3px;
    }
</style>