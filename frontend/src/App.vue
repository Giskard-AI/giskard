<template>
  <div id="app">
    <v-app>
      <v-main v-if="loggedIn === null || !backendReady">
        <v-container class="fill-height">
          <v-row align-center justify-center>
            <v-col>
              <div class="text-center">
                <div class="headline my-5" v-if="!backendReady">Waiting backend to start...</div>
                <div class="headline my-5" v-else>Loading...</div>
                <v-progress-circular
                    size="100"
                    indeterminate
                    color="primary"
                ></v-progress-circular>
              </div>
            </v-col>
          </v-row>
        </v-container>
      </v-main>
      <router-view/>
      <ModalsContainer/>
    </v-app>
  </div>
</template>

<script lang="ts" setup>
import {computed, onBeforeMount, provide} from "vue";
import {editor} from "monaco-editor";
import {useUserStore} from "@/stores/user";
import {useMainStore} from "@/stores/main";
import {storeToRefs} from "pinia";
import {ModalsContainer} from "vue-final-modal";
import IEditorOptions = editor.IEditorOptions;

const userStore = useUserStore();

const {backendReady} = storeToRefs(useMainStore())

const loggedIn = computed(() => {
  return userStore.isLoggedIn;
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
  userStore.isLoggedIn = false;
});
</script>
