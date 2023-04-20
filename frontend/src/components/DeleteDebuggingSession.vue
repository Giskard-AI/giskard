<script setup lang="ts">
import { api } from '@/api';
import { ref } from "vue";

interface Props {
  sessionId: number;
  sessionName: string;
}

const props = defineProps<Props>();

const dialog = ref(false);

const emit = defineEmits(['deleteDebuggingSession'])

async function deleteDebuggingSession() {
  await api.deleteInspection(props.sessionId);
  emit('deleteDebuggingSession', props.sessionId);
  dialog.value = false;
}

</script>

<template>
  <div class="text-center">
    <v-dialog v-model="dialog" width="500px">
      <template v-slot:activator="{ on, attrs }">
        <v-btn color="accent" v-bind="attrs" v-on="on" @click.stop icon>
          <v-icon>delete</v-icon>
        </v-btn>
      </template>
      <v-card>
        <v-card-title>Delete debugging session</v-card-title>
        <v-card-text>
          Are you sure you want to delete the debugging session
          <span class="font-weight-bold">{{ props.sessionName }}</span>?
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn color="primary" @click="deleteDebuggingSession">Delete</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<style scoped></style>