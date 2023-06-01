<template>
  <v-container>
    <div>Inputs</div>
    <v-list>
      <v-list-item v-for="(type, name) in inputs">
        <v-list-item-title>{{ name }}: {{ type }}</v-list-item-title>
      </v-list-item>
    </v-list>
  </v-container>
</template>

<script setup lang="ts">
import {useTestSuiteStore} from '@/stores/test-suite';
import {storeToRefs} from 'pinia';

const {inputs} = storeToRefs(useTestSuiteStore());

</script>
