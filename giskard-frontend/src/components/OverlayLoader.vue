<template>
    <div class="overlay">
        <v-progress-circular class="ma-2" :size="size" color="primary" indeterminate></v-progress-circular>
    </div>
</template>

<script lang="ts">
import { Vue, Component, Prop } from 'vue-property-decorator';

@Component
export default class OverlayLoader extends Vue {
    @Prop({default: 50}) size!: number 
}
</script>

<style scoped>
div.overlay {
    width: 100%;
    height: 100%;
    position: absolute;
    z-index: 1;
    background-color: #cdcdcd90;
    display: flex;
    justify-content: center;
    align-items: center;
}
</style>
