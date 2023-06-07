<template>
    <v-container>
        <v-layout align-center justify-center>
            <v-flex>
                <div class="text-center">
                    <div class="headline my-5">Loading {{ name }}...</div>
                    <v-progress-circular
                            size="100"
                            indeterminate
                            color="primary"
                    ></v-progress-circular>
                </div>
            </v-flex>
        </v-layout>
    </v-container>
</template>

<script setup lang="ts">
const props = defineProps<{ name: string }>();
</script>
