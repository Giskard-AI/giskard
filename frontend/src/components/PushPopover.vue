<template>
  <v-menu offset-x bottom :close-on-content-click="false" v-model="opened" v-if="show">
    <template v-slot:activator="{ on: onMenu }">
      <v-tooltip right>
        <template v-slot:activator='{ on: onTooltip }'>
          <v-btn small icon outlined color="warning" class="ml-1 ripple"
                 v-on="{ ...onMenu, ...onTooltip }" v-if="show">
            <div class="rim1"></div>
            <v-icon size="18" color="warning">mdi-alert-outline</v-icon>
          </v-btn>
        </template>
        <span>{{ push.push_title }}. Click for more details.</span>
      </v-tooltip>
    </template>


    <v-card dark color="primary" class="push-card">
      <v-card-title>
        {{ push.push_title }}
      </v-card-title>
      <v-card-text>
        <v-list light two-line>
          <template v-for="detail in push.push_details">
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
                <v-btn small text color="primary" :loading="detail.cta === loading" @click="applyCta(detail.cta)">
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
import {computed, ref, watch} from 'vue';
import {usePushStore} from "@/stores/push";
import {useMainStore} from "@/stores/main";
import {useCatalogStore} from "@/stores/catalog";
import {storeToRefs} from "pinia";
import {useProjectStore} from "@/stores/project";
import {useDebuggingSessionsStore} from "@/stores/debugging-sessions";
import {$vfm} from "vue-final-modal";
import AddTestToSuite from "@/views/main/project/modals/AddTestToSuite.vue";
import {chain} from "lodash";
import {TYPE} from "vue-toastification";
import {CallToActionKind, PushActionDTO, PushKind, RowFilterType} from "@/generated-sources";
import mixpanel from "mixpanel-browser";

const pushStore = usePushStore();
const mainStore = useMainStore();
const {slicingFunctionsByUuid, testFunctionsByUuid} = storeToRefs(useCatalogStore())
const catalogStore = useCatalogStore();
const projectStore = useProjectStore();
const debuggingStore = useDebuggingSessionsStore();

interface Props {
  type: string;
  column?: string;
}

const props = defineProps<Props>();

const opened = ref<boolean>(false);
const loading = ref<CallToActionKind>(CallToActionKind.None);
const value = computed(() => {
  return pushStore.current;
});

const show = computed(() => {
  if (value.value == undefined) return false;

  switch (props.type) {
    case "contribution":
      if (!value.value?.contribution || value.value?.contribution.kind == PushKind.Invalid) return false;
      return value.value?.contribution.key == props.column;
    case "perturbation":
      if (!value.value?.perturbation || value.value?.perturbation.kind == PushKind.Invalid) return false;
      return value.value?.perturbation.key == props.column;
    case "overconfidence":
      if (!value.value?.overconfidence || value.value?.overconfidence?.kind == PushKind.Invalid) return false;
      return value.value?.overconfidence.push_title && value.value.overconfidence.push_title != "";
    case "borderline":
      if (!value.value?.borderline || value.value?.borderline.kind == PushKind.Invalid) return false;
      return value.value?.borderline.push_title && value.value?.borderline.push_title != "";
    default:
      return false;
  }
})

const push = computed(() => {
  return value.value?.hasOwnProperty(props.type) ? value.value[props.type] : undefined;
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

async function applyCta(kind: CallToActionKind) {
  mixpanel.track("push:call_to_action", {kind: kind});
  loading.value = kind;
  let action: PushActionDTO = (await pushStore.applyPush(push.value!.kind, kind)).action;
  switch (kind) {
    case CallToActionKind.CreateSlice:
      mainStore.addSimpleNotification("Successfully saved");
      break;
    case CallToActionKind.CreateSliceOpenDebugger:
      await catalogStore.loadCatalog(projectStore.currentProjectId ?? 0);
      const slice = slicingFunctionsByUuid.value[action.object_uuid];
      if (slice !== undefined) {
        debuggingStore.setCurrentSlicingFunctionUuid(action.object_uuid);
        mainStore.addSimpleNotification("Slice applied");
      } else {
        mainStore.addNotification({content: 'Could not load slice', color: TYPE.ERROR});
      }
      break;
    case CallToActionKind.CreateTest:
    case CallToActionKind.AddTestToCatalog:
      await catalogStore.loadCatalog(projectStore.currentProjectId ?? 0);
      const test = testFunctionsByUuid.value[action.object_uuid];
      if (test !== undefined) {
        addToTestSuite(test, action.arguments);
      } else {
        mainStore.addNotification({content: 'Could not load test', color: TYPE.ERROR});
      }
      break;
    case CallToActionKind.SavePerturbation:
      mainStore.addSimpleNotification("Perturbation saved");
      break;
    case CallToActionKind.OpenDebuggerBorderline:
      debuggingStore.setSelectedFilter({value: RowFilterType.BORDERLINE, label: 'Underconfidence', disabled: false});
      break;
    case CallToActionKind.OpenDebuggerOverconfidence:
      // Programmatically apply Overconfidence filter
      break;
    case CallToActionKind.SaveExample:
      mainStore.addSimpleNotification("This feature is not yet implemented.");
      break;
    default:
      break;
  }
  loading.value = CallToActionKind.None;
  opened.value = false;
}

function addToTestSuite(test, parameters) {
  $vfm.show({
    component: AddTestToSuite,
    bind: {
      projectId: projectStore.currentProjectId ?? 0,
      test: test,
      suiteId: null,
      hideFixedInputs: true,
      testArguments: chain(test.args)
          .keyBy('name')
          .mapValues(arg => {
            let json = parameters[arg.name];
            let value = arg.optional ? arg.defaultValue : null;

            if (json != undefined) {
              let object = JSON.parse(json);
              if (object.hasOwnProperty('value')) {
                value = object.value;
              }
            }

            return {
              name: arg.name,
              isAlias: false,
              type: arg.type,
              value: value,
            };
          })
          .value()
    }
  });
}

watch(() => opened, (newValue, oldValue) => {
  if (newValue) {
    mixpanel.track("push:open", {type: props.type});
  }
})

</script>

<style scoped>
.v-tooltip__content,
.push-card {
  width: 40vw;
}

.rim1 {
  position: absolute;
  top: 50%;
  left: 50%;
  border-radius: 50%;
  width: 0em;
  height: 0em;
  border: white .5em solid;
  background: orange;
  z-index: 0;
}

.rim1 {
  animation: expand 2s ease-out infinite;
}

@keyframes expand {
  0% {
    top: calc(50% - .5em);
    left: calc(50% - .5em);
    width: 1em;
    height: 1em;
    border: white .25em solid;
    opacity: 0.5;
  }
  100% {
    top: calc(50% - 2em);
    left: calc(50% - 2em);
    width: 4em;
    height: 4em;
    border: white .5em solid;
    opacity: 0;
  }
}

.v-card__title {
  font-size: 1.125rem;
  line-height: 1.25rem;
}

.v-list-item__title,
.v-list-item__subtitle {
  white-space: normal;
}
</style>