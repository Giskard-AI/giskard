<template>
  <div id="app">
    <v-app>
        <v-main v-if="loggedIn === null || !backendReady">
            <v-container fill-height>
                <v-layout align-center justify-center>
                    <v-flex>
                        <div class="text-center">
                            <div class="headline my-5" v-if="!backendReady">Waiting backend to start...</div>
                            <div class="headline my-5" v-else>Loading...</div>
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
        <router-view/>
      <modals-container></modals-container>
    </v-app>
  </div>
</template>

<script lang="ts" setup>
import {computed, onBeforeMount, provide} from "vue";
import {editor} from "monaco-editor";
import {useUserStore} from "@/stores/user";
import {useMainStore} from "@/stores/main";
import {storeToRefs} from "pinia";
import IEditorOptions = editor.IEditorOptions;

const userStore = useUserStore();
const mainStore = useMainStore();

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
