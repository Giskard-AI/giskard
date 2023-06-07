<template>
    <vue-final-modal
        v-slot="{ close }"
        v-bind="$attrs"
        classes="modal-container"
        content-class="modal-content"
        v-on="$listeners"
        ref="modal"
        :click-to-close="false"
        :esc-to-close="false"
    >
        <div class="text-center">
            <v-card>
                <v-card-title>
                    {{ props.title }}
                </v-card-title>
                <v-card-text v-if="props.text" class="d-flex flex-column align-center">
                    <v-progress-circular indeterminate color="primary"/>
                    {{ props.text }}
                </v-card-text>
            </v-card>
        </div>
    </vue-final-modal>
</template>

<script setup lang="ts">

import {onMounted, ref} from 'vue';

const props = defineProps<{
    title: string,
    text?: string,
}>();

const modal = ref()

const emit = defineEmits(['mounted']);

onMounted(() => {
    emit('mounted', modal.value.close)
})

</script>

<style scoped>
::v-deep(.modal-container) {
    display: flex;
    justify-content: center;
    align-items: center;
}

::v-deep(.modal-content) {
    position: relative;
    display: flex;
    flex-direction: column;
    margin: 0 1rem;
    padding: 1rem;
}

</style>
