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
                    Create an alias for {{ props.name }}
                </v-card-title>
                <v-card-text class="card-content">

                </v-card-text>
                <v-card-actions>
                    <v-btn @click="close" color="error">Cancel</v-btn>
                    <v-btn color="primary">Create</v-btn>
                </v-card-actions>
            </v-card>
        </div>
    </vue-final-modal>
</template>

<script setup lang="ts">

const props = defineProps<{
    name: string,
    type: string
}>();

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
    min-width: 50vw;
    max-height: 80vh;
    overflow: auto;

}

.card-content {
    text-align: start;
}

</style>
