<template>
    <p>
        <span v-for="(n, index) in props.weights.length"
              :class="(Object.values(weights[index])[0] !== 0) ? 'impactWord' : ''"
              :style="{ backgroundColor: calculateBackgroundColor(Object.values(weights[index])[0]) }"
              :key="n">{{Object.keys(weights[index])[0]}}</span>
    </p>
</template>


<script setup lang="ts">


const props = defineProps<{
    weights: { [key: string]: number }[]
}>();

function calculateBackgroundColor(weight: number){
    if (weight === 0){
        return 'transparent';
    }
    else if (weight > 0){
        return '#00FF00' + (weight * 25.6).toString(16).split('.')[0];
    }
    else{
        return '#FF0000' + (weight * - 25.6).toString(16).split('.')[0];
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