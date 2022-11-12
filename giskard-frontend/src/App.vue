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
      <NotificationsManager></NotificationsManager>
    </v-app>
  </div>
</template>

<script lang="ts" setup>
import NotificationsManager from '@/components/NotificationsManager.vue';
import {computed, onBeforeMount} from "vue";
import {useLoginStore} from "@/store/pinia/login";

const loginStore = useLoginStore();
const loggedIn = computed(() => {
  return loginStore.isLoggedIn;
});
onBeforeMount( async () => {
  await loginStore.checkLoggedIn();
})


// ((this!.$root as any).monacoOptions as IEditorOptions) = {
//   automaticLayout: true,
//   minimap: {
//     enabled: false
//   },
//   renderLineHighlight: "none"
// };
</script>
