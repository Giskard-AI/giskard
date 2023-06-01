<template>
    <vue-final-modal
        v-slot="{ close }"
        v-bind="$attrs"
        classes="modal-container"
        content-class="modal-content"
        v-on="$listeners"
    >
        <v-card class="modal-card">
            <v-card-title>
                Differences
            </v-card-title>
            <v-card-text class="card-content">
                <v-row>
                    <v-col cols=6>
                        <span v-for="diff in diffs" v-if="!diff.added"
                              :class="{'removed': diff.removed}">{{ diff.value }}</span>
                    </v-col>
                    <v-col cols=6>
                        <span v-for="diff in diffs" v-if="!diff.removed"
                              :class="{'added': diff.added}">{{ diff.value }}</span>
                    </v-col>
                </v-row>
            </v-card-text>

            <v-divider></v-divider>

            <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn
                    color="primary"
                    text
                    @click="close"
                >
                    Close
                </v-btn>
            </v-card-actions>
        </v-card>
    </vue-final-modal>
</template>

<script setup lang="ts">

import {computed} from "vue";

const Diff = require('diff');

const props = defineProps<{
    oldValue: string,
    newValue: string
}>()

const diffs = computed(() => Diff.diffChars(props.oldValue, props.newValue));

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

.added {
    background: #2ea769;
}

.removed {
    background: #ff5631;
}

.modal-card {
    max-height: 80vh;
    display: flex;
    flex-direction: column;
}

.card-content {
    flex-grow: 1;
    overflow: auto;
}
</style>
