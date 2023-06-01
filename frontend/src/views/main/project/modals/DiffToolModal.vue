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
                        <p>
                            <span v-for="(diff, i) in removed" :key="i" :class="{removed: diff.removed}">{{
                                    diff.value
                                }}</span>
                        </p>
                    </v-col>
                    <v-col cols=6>
                        <p>
                            <span v-for="(diff, i) in added" :key="i" :class="{added: diff.added}">{{
                                    diff.value
                                }}</span>
                        </p>
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

import {onMounted, ref} from "vue";
import {chain} from "lodash";

const Diff = require('diff');

const props = defineProps<{
    oldValue: string,
    newValue: string
}>()


const added = ref<Array<any>>([])
const removed = ref<Array<any>>([])

onMounted(() => {
    const diffs = Diff.diffChars(props.oldValue, props.newValue, {})

    removed.value = chain(diffs)
        .filter(diff => !diff.added)
        .value();
    added.value = chain(diffs)
        .filter(diff => !diff.removed)
        .value();
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

.added {
    color: #155724;
    background: #d4edda;
}

.removed {
    color: #721c24;
    background: #f8d7da;
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
