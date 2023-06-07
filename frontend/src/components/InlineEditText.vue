<template>
  <div>
    <template v-if=isBeingEdited>
      <div class="row-container">
        <v-text-field v-model="editedText" @click.stop @keyup.prevent @keydown.enter="save()" @keydown.esc="editedText = null" :rules="[v => '' !== v.trim() || 'Required']" :hide-details="true" dense single-line>
        </v-text-field>
        <v-tooltip bottom>
          <template v-slot:activator="{ on, attrs }">
            <v-btn icon color="accent" @click.stop="editedText = null" v-bind="attrs" v-on="on">
              <v-icon>cancel</v-icon>
            </v-btn>
          </template>
          <span>Cancel</span>
        </v-tooltip>
        <v-tooltip bottom>
          <template v-slot:activator="{ on, attrs }">
            <v-btn icon color="primary" @click.stop="save()" :disabled="!isAllowedToSave" v-bind="attrs" v-on="on">
              <v-icon>save</v-icon>
            </v-btn>
          </template>
          <span>Save</span>
        </v-tooltip>
      </div>
    </template>
    <template v-else>
      <div class="row-container">
        <span>{{ props.text }}</span>
        <v-tooltip bottom v-if="props.canEdit">
          <template v-slot:activator="{ on, attrs }">
            <v-btn icon color="primary" @click.stop="editedText = props.text" v-bind="attrs" v-on="on">
              <v-icon>edit</v-icon>
            </v-btn>
          </template>
          <span>{{ editText }}</span>
        </v-tooltip>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">

import { computed, ref } from 'vue';

const props = withDefaults(defineProps<{
  text: string,
  canEdit?: boolean,
  editText?: string
}>(), {
  canEdit: true,
  editText: "Rename"
});

const editedText = ref<string | null>(null);

const emit = defineEmits(['save'])

const isBeingEdited = computed(() => editedText.value !== null);

const isAllowedToSave = computed(() => editedText.value && editedText.value.trim() !== '');

function save() {
  emit('save', editedText.value);
  editedText.value = null;
}
</script>

<style lang="scss" scoped>
.row-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
