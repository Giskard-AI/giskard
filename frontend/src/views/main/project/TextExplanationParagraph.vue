<template>
    <div ref="paragraph">
        <div style="width: 95%;">
            <v-slider
                v-model="range"
                thumb-size="10"
                min="0"
                max="100"
                label="Importance"
            ></v-slider>
        </div>
<!--        <VirtualCollection-->
<!--            :cellSizeAndPositionGetter="cellSizeAndPositionGetter"-->
<!--            :collection="items"-->
<!--            :height="200"-->
<!--            :width="widthParagraph"-->
<!--            class="overflow-x-hidden"-->
<!--        >-->
<!--        <template v-slot:cell="item">-->
<!--            <span  :style="{ backgroundColor: item.data.color }">{{item.data.text}}</span>-->
<!--        </template>-->
<!--        </VirtualCollection>-->
    </div>
</template>



<script setup lang="ts">
import { ref, getCurrentInstance, watch, onMounted } from 'vue';
// import VirtualCollection from "vue-virtual-collection/src/VirtualCollection.vue";

const props = defineProps<{
    weights: number[]
    words: string[]
    max_weight: number
    min_weight: number
}>();

const paragraph = ref<HTMLDivElement>()
const range = ref<number>(0)
const widthParagraph = ref<number>(getCurrentInstance()?.proxy.$parent?.$el.clientWidth! - 40);
const x = ref<number>(0)
const y = ref<number>(0)
const classificationMinWeight = ref<number>(Math.min(...props.weights));
const classificationMaxWeight = ref<number>(Math.max(...props.weights));
const absoluteMaxWeight = ref<number>(Math.max(Math.abs(props.max_weight), Math.abs(props.min_weight)))
const items =  ref<object[]>(createItems())

// Changement of Classification Label
watch(() => [...props.weights], () => {
    classificationMinWeight.value = Math.min(...props.weights)
    if (classificationMinWeight.value === 0)
        classificationMinWeight.value = -1;
    classificationMaxWeight.value = Math.max(...props.weights)
    if (classificationMaxWeight.value === 0)
        classificationMaxWeight.value = 1;
})

// Changement of Classification Label or Modification of the slider
watch(() => [...props.weights, range.value], updateTextColor)


function updateTextColor(){
    for (let i = 0; i < props.words.length; i++){
        items.value[i].data.color = calculateBackgroundColor(props.weights[i])  
    } 
}

function calculateBackgroundColor(weight: number){
    let multiplicatior = (weight < 0) ? weight / classificationMinWeight.value : weight / classificationMaxWeight.value;
    multiplicatior *= 100;
    if (multiplicatior < range.value || absoluteMaxWeight.value === 0){
        return 'transparent';
    }
    else {
        let color = (weight > 0) ? 'rgba(0, 256, 0, ' : 'rgba(256, 0, 0, ';
        color += Math.abs(weight) / absoluteMaxWeight.value + ')'; 
        return color
    }
}

onMounted(() => {
    window.addEventListener('resize', () => {
        x.value = 0;
        y.value = 0;
        widthParagraph.value = paragraph.value!.clientWidth;
        items.value = createItems()
    });
})

// Called when mounted and when window resized 
function createItems(){
    const canvas = document.createElement("canvas") as HTMLCanvasElement;
    const wordHorizontalPadding = 3;
    const lineHeight = 20;
    return Array.from({length: props.words.length}, (_, index) => {
        let widthText = getTextWidth(props.words[index], canvas) + wordHorizontalPadding;
        if (x.value + widthText >= widthParagraph.value){
            x.value = 0;
            y.value += lineHeight; 
        }
        let res = { 
            data: {
                text: props.words[index],
                color: calculateBackgroundColor(props.weights[index]),
                weight: props.weights[index]
            },
            height: 20,
            width: widthText,
            x: x.value,
            y: y.value
        }
        x.value += widthText;
        return res;
    })
}

function getTextWidth(text, c: HTMLCanvasElement) {
    let ctx = c.getContext("2d")!;
    ctx.font = "14px Roboto, sans-serif";
    let txt = text;
    return ctx.measureText(txt).width;
};



function cellSizeAndPositionGetter(item, _) {
    const { data, ...sizeAndPlace} = item;
    return sizeAndPlace
}
</script>