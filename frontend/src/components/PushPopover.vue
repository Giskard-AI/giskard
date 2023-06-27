<template>
  <v-menu offset-x bottom :close-on-content-click="false" v-model="opened" v-if="show">
    <template v-slot:activator="{ on: onMenu }">
      <v-tooltip right>
        <template v-slot:activator='{ on: onTooltip }'>
          <v-btn small icon v-on="{ ...onMenu, ...onTooltip }">
            <v-badge bottom overlap color="transparent">
              <v-icon size="18">mdi-auto-fix</v-icon>
              <template v-slot:badge>
                <v-icon color="primary" class="mt-n1 ml-n2" style="height: 6px;" small>{{ icon }}</v-icon>
              </template>
            </v-badge>
          </v-btn>
        </template>
        <span>Suggestions</span>
      </v-tooltip>
    </template>


    <v-card dark color="primary">
      <v-card-title>
        {{ push.pushTitle }}
      </v-card-title>
      <v-card-text>
        <v-list light two-line>
          <template v-for="detail in push.details">
            <v-list-item>
              <v-list-item-content>
                <v-list-item-title>
                  {{ detail.action }}
                </v-list-item-title>
                <v-list-item-subtitle>
                  {{ detail.explanation }}
                </v-list-item-subtitle>
              </v-list-item-content>
              <v-list-item-action>
                <v-btn small text color="primary" @click="applyCta(detail.kind)">
                  {{ detail.button }}
                </v-btn>
              </v-list-item-action>
            </v-list-item>
            <v-divider/>
          </template>
        </v-list>
      </v-card-text>
    </v-card>

  </v-menu>
</template>

<script setup lang="ts">

//////// TODO BEFORE MERGE:
// - Add a mixpanel event when the menu is opened (with the push type?)
// - Add a mixpanel event when a CTA is clicked (with the CTA type?)

import {computed, ref} from 'vue';
import {usePushStore} from "@/stores/push";

const pushStore = usePushStore();

const props = defineProps({
  type: String,
  column: String,
});

const opened = ref<boolean>(false);
const value = computed(() => {
  return pushStore.current;
});

const show = computed(() => {
  switch (props.type) {
    case "contribution":
      return value.value?.contribution.key == props.column;
    case "perturbation":
      return value.value?.perturbation.key == props.column;
    case "overconfidence":
      return value.value?.overconfidence.pushTitle && value.value?.overconfidence.pushTitle != "";
    case "borderline":
      return value.value?.borderline.pushTitle && value.value?.borderline.pushTitle != "";
    default:
      return false;
  }
})
const push = computed(() => {
  switch (props.type) {
    case "contribution":
      return value.value?.contribution;
    case "perturbation":
      return value.value?.perturbation;
    case "overconfidence":
      return value.value?.overconfidence;
    case "borderline":
      return value.value?.borderline;
    default:
      return false;
  }
})

const icon = computed(() => {
  switch (props.type) {
    case "contribution":
      return "mdi-chart-bar";
    case "perturbation":
      return "mdi-waveform";
    case "overconfidence":
      return "mdi-chevron-triple-up";
    case "borderline":
      return "mdi-approximately-equal";
    default:
      return "mdi-bug";
  }
});

async function applyCta(kind: string) {
  // modelId: string, datasetId: string, rowNb: number, pushKind: string, ctaKind: string
  await pushStore.applyPush(push.value!.kind, kind);
}
</script>

<style scoped>
</style>