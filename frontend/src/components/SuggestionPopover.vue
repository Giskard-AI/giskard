<template>
  <v-menu offset-x bottom :close-on-content-click="false" v-model="opened" v-if="show">
    <template v-slot:activator="{ on: onMenu }">
      <v-tooltip right>
        <template v-slot:activator='{ on: onTooltip }'>
          <v-btn small icon v-on="{ ...onMenu, ...onTooltip }">
            <v-badge bottom overlap color="transparent">
              <v-icon size="18">mdi-auto-fix</v-icon>
              <template v-slot:badge>
                <v-icon color="primary" class="mt-n1 ml-n2">{{ icon }}</v-icon>
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
                <v-tooltip top>
                  <template v-slot:activator="{ on, attrs }">
                    <v-btn small text color="primary" disabled v-bind="attrs" v-on="on">
                      {{ detail.button }}
                    </v-btn>
                  </template>
                  This action will be available in Giskard 2.1
                </v-tooltip>
              </v-list-item-action>
            </v-list-item>
            <v-divider/>
          </template>
        </v-list>
      </v-card-text>
    </v-card>

  </v-menu>
  <!--  <div v-else style="width: 30px"></div>-->
</template>

<script setup lang="ts">
import {computed, ref} from 'vue';
import {usePushStore} from "@/stores/suggestions";
import {PushDTO} from "@/generated-sources";

const pushStore = usePushStore();

const value = ref<PushDTO | undefined>(undefined);
import {usePushStore} from "@/stores/suggestions";
import {usePushStore} from "@/stores/suggestions";

const pushStore = usePushStore();

// const value = ref<PushDTO | undefined>(undefined);

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

// watch(() => props.suggestion, () => {
//   value.value = props.suggestion ? props.suggestion.filter((s) => s.key == props.column)[0] : undefined;
// });
//
// async function dbg_GetSuggestion() {
//   await api.applyPush(props.modelId ?? "", props.datasetId ?? "", props.rowNb ?? 0, 0, 1)
// }


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
</script>

<style scoped>
</style>