<template>
  <div class="text-center">
    <v-btn
        icon
        @click.stop="opened = true"
        @click.stop.prevent
    >
      <slot></slot>
    </v-btn>
    <v-dialog
        v-model="opened"
    >
      <v-card>
        <v-card-title>
          {{ props.title }}
        </v-card-title>
        <v-card-text v-if="props.text">
          {{ props.text }}
        </v-card-text>
        <v-card-actions>
          <v-btn color="primary" @click="handleActionsClick(false)">{{ props.cancelMessage }}</v-btn>
          <v-btn :color=buttonColor @click="handleActionsClick(true)">{{ props.confirmMessage }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">

import {computed, ref} from 'vue';

const props = withDefaults((defineProps<{
  confirmMessage?: string,
  cancelMessage?: string,
  title: string,
  text?: string,
  isWarning?: boolean
}>()), {
  confirmMessage: 'Confirm',
  cancelMessage: 'Cancel',
  isWarning: false
});

const opened = ref<Boolean>(false);

const emit = defineEmits(['dismiss']);


const buttonColor = computed<string>(() => {
  return props.isWarning ? 'accent' : 'primary';
});

function handleActionsClick(confirm: boolean) {
  opened.value = false;
  emit('dismiss', confirm);
}

</script>
