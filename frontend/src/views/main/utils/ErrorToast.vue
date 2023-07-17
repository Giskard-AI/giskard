<template>
  <div>
    <div class="title">{{ title }}</div>
    <div class="detail" v-show="detail">{{ detail }}</div>
    <div style="width: 100%">
      <div v-show="stack" class="stack">
        <pre class="stack">{{ stack }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  title: string;
  detail?: string;
  stack?: string;
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

.detail {
  padding-top: 10px;
  overflow: auto;
  white-space: break-spaces;
  max-height: 70px;
}
</style>
