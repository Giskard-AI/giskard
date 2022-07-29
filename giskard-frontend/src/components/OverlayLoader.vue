<template>
  <v-overlay :value="show" :absolute="absolute" :color="solid ? '#ffffff':'#cdcdcd90'" :opacity="solid ? 1: 0.46"
             :class="classes">
    <v-progress-circular class="ma-2" :size="size" color="primary" indeterminate></v-progress-circular>
  </v-overlay>
</template>

<script lang="ts">
import {Component, Prop, Vue} from 'vue-property-decorator';

@Component
export default class OverlayLoader extends Vue {
  @Prop({default: 50}) size!: number;
  @Prop({type: Boolean}) solid!: boolean;
  @Prop({type: Boolean}) show!: boolean;
  @Prop({type: Boolean}) absolute!: boolean;
  @Prop({type: Boolean, default: false}) noFade!: boolean;

  get classes() {
    return {
      'no-fade': this.noFade
    }
  }
}
</script>

<style lang="scss">
.v-overlay {
  &.no-fade {
    transition-duration: 0s;
  }
}
</style>