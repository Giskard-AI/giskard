<template>
    <vue-final-modal
            v-slot="{ close }"
            v-bind="$attrs"
            classes="modal-container"
            content-class="modal-content"
            v-on="$listeners"
    >
        <div class="text-center">
            <v-card>
                <v-card-title>
                    {{ props.title }}
                </v-card-title>
                <v-card-text v-if="props.text">
                    {{ props.text }}
                </v-card-text>
                <v-card-actions>
                    <div class="flex-grow-1"/>
                    <v-btn text color="primary" @click="close">{{ props.cancelMessage }}</v-btn>
                    <v-btn :color=buttonColor @click="emit('confirm', close)">{{ props.confirmMessage }}</v-btn>
                </v-card-actions>
            </v-card>
        </div>
    </vue-final-modal>
</template>

<script setup lang="ts">

import {computed} from 'vue';

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

const emit = defineEmits(['input']);

const buttonColor = computed<string>(() => {
    return props.isWarning ? 'accent' : 'primaryLight';
});

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
