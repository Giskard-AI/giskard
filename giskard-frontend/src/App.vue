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

<script lang="ts">
import { Component, Vue } from 'vue-property-decorator';
import NotificationsManager from '@/components/NotificationsManager.vue';
import { readAppSettings, readIsLoggedIn } from '@/store/main/getters';
import { dispatchCheckLoggedIn } from '@/store/main/actions';
import { editor } from 'monaco-editor';
import IEditorOptions = editor.IEditorOptions;

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
    const appSettings = await readAppSettings(this.$store);

    let roles = Object.assign({}, ...appSettings!.roles.map((x) => ({[x.id]: x.name})));
    Vue.filter('roleName', function(value) {
      if (value in roles) {
        return roles[value];
      } else {
        return value;
      }
    });

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
