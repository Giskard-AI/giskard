<template>
  <div>
    <v-btn :color="color" @click="trigger">
      <slot>Choose File</slot>
    </v-btn>
    <input :multiple="multiple" class="visually-hidden" type="file" v-on:change="handleFiles" ref="fileInput">
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

interface Props {
  color: string;
  multiple: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  multiple: false
});

const files = ref<FileList | null>(null);
const fileInput = ref<HTMLInputElement | null>(null);

const trigger = () => {
  fileInput.value!.click();
};

const handleFiles = (e: Event) => {
  const target = e.target as HTMLInputElement;
  if (target.files) {
    files.value = target.files;
    emit('files', target.files);
  }
};

const emit = defineEmits(['files']);
</script>

<style scoped>
.visually-hidden {
  position: absolute !important;
  height: 1px;
  width: 1px;
  overflow: hidden;
  clip: rect(1px, 1px, 1px, 1px);
}
</style>
