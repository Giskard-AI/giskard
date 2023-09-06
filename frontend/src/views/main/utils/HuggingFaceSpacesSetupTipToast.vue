<template>
  <div>
    <div class="title">{{ title }}</div>
    <div class="detail" v-show="detail">{{ detail }}</div>
    <a href="/hfspaces/setup-tip">See more</a>
  </div>
</template>

<script setup lang="ts">
interface Props {
  title: string;
  detail?: string;
}

const props = defineProps<Props>();
</script>

<style scoped lang="scss">
.title {
  overflow-x: auto;
  font-size: 20px;
}

.stack {
  padding-top: 10px;
  display: block;
  max-height: 300px;
  width: 100%;
  overflow: auto;
  font-size: 0.75em;
}
</style>
