<template>
    <vue-final-modal
            v-slot="{ close }"
            v-bind="$attrs"
            classes="modal-container"
            content-class="modal-content"
            v-on="$listeners"
    >
        <v-form @submit.prevent="">
            <ValidationObserver ref="observer" v-slot="{ invalid }">
                <v-card>
                    <v-card-title>
                        Advanced setting for '{{ input }}' Dataset input
                    </v-card-title>

                    <v-card-text>

                    </v-card-text>

                    <v-divider></v-divider>

                    <v-card-actions>
                        <v-spacer></v-spacer>
                        <v-btn
                                color="secondary"
                                text
                                @click="close"
                        >
                            Cancel
                        </v-btn>
                    </v-card-actions>
                </v-card>
            </ValidationObserver>
        </v-form>
    </vue-final-modal>
</template>

<script setup lang="ts">

const props = defineProps<{
    input: string
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
}

</style>
