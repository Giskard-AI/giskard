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
      <router-view v-else />
      <NotificationsManager></NotificationsManager>
    </v-app>
  </div>
</template>

<script lang="ts">
import { Component, Vue } from "vue-property-decorator";
import NotificationsManager from "@/components/NotificationsManager.vue";
import { readIsLoggedIn } from "@/store/main/getters";
import { dispatchCheckLoggedIn } from "@/store/main/actions";
import posthog from "posthog-js";
import {editor} from "monaco-editor";
import IEditorOptions = editor.IEditorOptions;


if (
  !window.location.href.includes("127.0.0.1") &&
  !window.location.href.includes("localhost")
) {
  posthog.init("phc_sIBMMHiIjqo3UYROGlNLb7Uo51FYpAfkTDmOMZmiKpD", {
    api_host: "https://app.posthog.com",
  });
}

@Component({
  components: {
    NotificationsManager,
  },
})
export default class App extends Vue {
  get loggedIn() {
    return readIsLoggedIn(this.$store);
  }

  public async created() {
    await dispatchCheckLoggedIn(this.$store);
    ((this.$root as any).monacoOptions as IEditorOptions) = {
      automaticLayout: true,
      minimap: {
        enabled: false
      },
      renderLineHighlight: "none"
    };
  }
}
</script>
