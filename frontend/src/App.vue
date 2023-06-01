<template>
  <div id="app">
    <v-app>
      <v-main v-if="loggedIn === null">
        <v-container fill-height>
          <v-layout align-center justify-center>
            <v-flex>
              <div class="text-center">
                <div class="headline my-5">Loading...</div>
                <v-progress-circular
                    size="100"
                    indeterminate
                    color="primary"
                ></v-progress-circular>
              </div>
            </v-flex>
          </v-layout>
        </v-container>
      </v-main>
      <router-view v-else/>
      <modals-container></modals-container>
    </v-app>
  </div>
</template>

<script lang="ts" setup>
import {readIsLoggedIn} from '@/store/main/getters';
import {dispatchCheckLoggedIn} from '@/store/main/actions';
import {computed, onBeforeMount, provide} from "vue";
import store from "@/store";
import {editor} from "monaco-editor";
import IEditorOptions = editor.IEditorOptions;

const loggedIn = computed(() => {
  return readIsLoggedIn(store);
});

let monacoOptions: IEditorOptions = {
  automaticLayout: true,
  minimap: {
    enabled: false
  },
  renderLineHighlight: "none"
};
provide('monacoOptions', monacoOptions);

onBeforeMount(async () => {
  await dispatchCheckLoggedIn(store);
});
</script>
