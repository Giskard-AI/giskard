<template>
  <div>
    <div class="title">{{ title }}</div>
    <pre class="detail" v-show="detail">{{ detail }}</pre>
  </div>
</template>

<script lang="ts">

import Component from "vue-class-component";
import Vue from "vue";
import {Prop} from "vue-property-decorator";

@Component
export default class ErrorToast extends Vue {
  @Prop({required: true}) title!: string;
  @Prop() detail?: string;
}
</script>

<style scoped lang="scss">
.detail{
  font-size: 15px;
  background-color: rgba(211, 211, 211, 0.52);
  display: block;
  padding: 10px;
  margin-top: 10px;
  color: rgba(0,0,0,.87);
  max-width: 490px;
  overflow: auto;
}
</style>