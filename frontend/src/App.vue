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
    </v-app>
  </div>
</template>

<script lang="ts" setup>
import {computed, onBeforeMount, provide} from "vue";
import {editor} from "monaco-editor";
import IEditorOptions = editor.IEditorOptions;
import {useUserStore} from "@/stores/user";

const userStore = useUserStore();

const loggedIn = computed(() => {
  return userStore.loggedIn;
})

let monacoOptions: IEditorOptions = {
  automaticLayout: true,
  minimap: {
    enabled: false
  },
  renderLineHighlight: "none"
};
provide('monacoOptions', monacoOptions);

onBeforeMount(async () => {
  await userStore.checkLoggedIn();
});
</script>
