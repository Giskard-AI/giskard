<template>
  <v-menu offset-x :close-on-content-click="false" v-model="opened" v-if="value">
    <template v-slot:activator="{ on: onMenu }">
      <v-tooltip right>
        <template v-slot:activator='{ on: onTooltip }'>
          <v-btn small icon v-on="{ ...onMenu, ...onTooltip }" :disabled="props.disabled">
            <v-badge color="error" :content="value.details.length" overlap>
              <v-icon size="18">mdi-auto-fix</v-icon>
            </v-badge>
          </v-btn>
        </template>
        <span>Suggestions</span>
      </v-tooltip>
    </template>


    <v-card dark color="primary">
      <v-card-title>
        {{ value.pushTitle }}
      </v-card-title>
      <v-card-text>
        <v-list light two-line>
          <template v-for="detail in value.details">
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
                <v-btn small text color="primary" @click.stop="dbg_GetSuggestion">
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
  <div v-else style="width: 30px"></div>
</template>

<script setup lang="ts">
import {computed, ref, watch} from 'vue';
import {usePushStore} from "@/stores/suggestions";
import {PushDTO} from "@/generated-sources";

const pushStore = usePushStore();

const value = ref<PushDTO | undefined>(undefined);
import {usePushStore} from "@/stores/suggestions";
import {PushDTO} from "@/generated-sources";

const pushStore = usePushStore();

const value = ref<PushDTO | undefined>(undefined);

const props = defineProps({
  modelId: String,
  datasetId: String,
  rowNb: Number,
  disabled: Boolean,
  column: String
});

const opened = ref<boolean>(false);

watch(() => props.rowNb, () => {
  const list = pushStore.getPushSuggestions(props.modelId ?? "", props.datasetId ?? "", props.rowNb ?? 0);
  value.value = list ? list.filter((s) => s.key == props.column)[0] : undefined;
});

async function dbg_GetSuggestion() {

}

const val = computed(() => {
  const list = pushStore.getPushSuggestions(props.modelId ?? "", props.datasetId ?? "", props.rowNb ?? 0);
  return list ? list.filter((s) => s.key == props.column)[0] : undefined;
});
</script>

<style scoped>

</style>