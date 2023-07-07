<template>
  <v-menu offset-x bottom :close-on-content-click="false" v-model="opened" v-if="show">
    <template v-slot:activator="{ on: onMenu }">
      <v-tooltip right>
        <template v-slot:activator='{ on: onTooltip }'>
          <v-btn small icon outlined color="warning" class="ml-1"
                 v-on="{ ...onMenu, ...onTooltip }">
            <v-icon size="18" color="warning">mdi-alert-outline</v-icon>
            <!--<v-badge top overlap color="transparent">
              <v-icon size="18" color="primary">mdi-warning</v-icon>
              <template v-slot:badge>
                <v-icon color="error" style="height: 6px;" small>mdi-exclamation</v-icon>
              </template>
            </v-badge>-->
          </v-btn>
        </template>
        <span>{{ push.pushTitle }}</span>
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
                <v-btn small text color="primary" :loading="detail.kind === loading" @click="applyCta(detail.kind)">
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
import {useMainStore} from "@/stores/main";
import {useCatalogStore} from "@/stores/catalog";
import {storeToRefs} from "pinia";
import {useProjectStore} from "@/stores/project";
import {useDebuggingSessionsStore} from "@/stores/debugging-sessions";

const pushStore = usePushStore();
const mainStore = useMainStore();
const {slicingFunctionsByUuid} = storeToRefs(useCatalogStore())
const catalogStore = useCatalogStore();
const projectStore = useProjectStore();
const debuggingStore = useDebuggingSessionsStore();

//:modelFeatures="modelFeatures"
//:inputData="inputData"
const props = defineProps({
  type: String,
  column: String
});

const opened = ref<boolean>(false);
const loading = ref<string>("");
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
  loading.value = kind;
  // modelId: string, datasetId: string, rowNb: number, pushKind: string, ctaKind: string
  // @ts-ignore
  let uuid = await pushStore.applyPush(push.value!.kind, kind);


  switch (kind) {
    case "CreateSlice":
    case "SaveExample":
      mainStore.addSimpleNotification("Successfully saved");
      break;
    case "CreateSliceOpenDebugger":
      await catalogStore.loadCatalog(projectStore.currentProjectId ?? 0);
      const slice = slicingFunctionsByUuid.value[uuid];
      if (slice !== undefined) {
        console.log("Setting object")
        debuggingStore.setCurrentSlicingFunctionUuid(uuid);
        // TODO: Figure out how to load a slice from here
        mainStore.addSimpleNotification("Slice applied");
      } else {
        // Error slice not found
      }
      break;
    case "CreateTest":
      mainStore.addSimpleNotification("Test created, add it to a test suite?");
      break;
    case "SavePerturbation":
      mainStore.addSimpleNotification("Perturbation saved");
      break;
    default:
      break;
  }
  loading.value = "";
  opened.value = false;
}
</script>

<style scoped>
</style>