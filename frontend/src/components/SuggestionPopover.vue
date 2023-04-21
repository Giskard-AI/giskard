<template>
  <v-menu offset-x :close-on-content-click="false" v-model="opened">
    <template v-slot:activator="{ on: onMenu }">
      <v-tooltip right>
        <template v-slot:activator='{ on: onTooltip }'>
          <v-btn small icon v-on="{ ...onMenu, ...onTooltip }" :disabled="props.disabled">
            <!--            <v-badge color="error" content="1" overlap :>-->
            <v-icon size="18">mdi-auto-fix</v-icon>
            <!--            </v-badge>-->
          </v-btn>
        </template>
        <span>Suggestions</span>
      </v-tooltip>
    </template>


    <v-card dark color="primary">
      <v-card-title>
        <!--        Potential improvements for-->
        <v-chip>account_check_status == '< 0 DM'</v-chip>
        is responsible for the prediction being wrong.
      </v-card-title>
      <v-card-text>
        <v-list light two-line>
          <v-list-item>
            <v-list-item-content>
              <v-list-item-title>
                <!--                This value is responsible for the prediction being wrong.-->
                Open a new debugger session with similar examples
              </v-list-item-title>
              <v-list-item-subtitle>
                <!--                Open the inspector with similar examples ?-->
                Debugging similar examples may help you find common patterns
              </v-list-item-subtitle>
            </v-list-item-content>
            <v-list-item-action>
              <v-btn small text color="primary" @click.stop="dbg_GetSuggestion">
                <!--                <v-icon>mdi-check</v-icon>-->
                Open debugger
              </v-btn>
              <!--              <v-btn small icon color="error">-->
              <!--                <v-icon>mdi-close</v-icon>-->
              <!--              </v-btn>-->
            </v-list-item-action>
          </v-list-item>
          <v-divider/>
          <v-list-item>
            <v-list-item-content>
              <v-list-item-title>Generate a new performance difference test in the catalog</v-list-item-title>
              <v-list-item-subtitle>This may help ensure this incorrect pattern is not common to the whole dataset
              </v-list-item-subtitle>
            </v-list-item-content>
            <v-list-item-action>
              <v-btn small text color="primary" @click.stop="dbg_GetSuggestion">
                <!--                <v-icon>mdi-check</v-icon>-->
                CREATE TEST
              </v-btn>
            </v-list-item-action>
          </v-list-item>
          <v-divider/>
          <v-list-item>
            <v-list-item-content>
              <v-list-item-title>Save slice and continue debugging session</v-list-item-title>
              <v-list-item-subtitle>Saving the slice will enable you to create tests more efficiently
              </v-list-item-subtitle>
            </v-list-item-content>
            <v-list-item-action>
              <v-btn small text color="primary" @click.stop="dbg_GetSuggestion">
                <!--                <v-icon>mdi-check</v-icon>-->
                SAVE SLICE
              </v-btn>
            </v-list-item-action>
          </v-list-item>
          <v-divider/>
          <v-list-item>
            <v-list-item-content>
              <v-list-item-title>What action do we want to do</v-list-item-title>
              <v-list-item-subtitle>What it brings to the user</v-list-item-subtitle>
            </v-list-item-content>
            <v-list-item-action>
              <v-btn small text color="primary" @click.stop="dbg_GetSuggestion">
                <!--                <v-icon>mdi-check</v-icon>-->
                CALL TO ACTION
              </v-btn>
            </v-list-item-action>
          </v-list-item>
        </v-list>
      </v-card-text>
    </v-card>

  </v-menu>
</template>

<script setup lang="ts">
import {ref} from 'vue';
import {api} from "@/api";

const props = defineProps({
  modelId: String,
  datasetId: String,
  disabled: Boolean
});

const opened = ref<boolean>(false);

const suggestions = [
  {
    problem: "This feature contributes a lot to the prediction",
    suggestion: "Create a slice automatically ?"
  },
  {
    problem: "This correlation may apply to the whole dataset",
    suggestion: "Create a test automatically ?"
  }
]

async function dbg_GetSuggestion() {
  await api.getSuggestions(props.modelId ?? "", props.datasetId ?? "", 0);
}
</script>

<style scoped>

</style>