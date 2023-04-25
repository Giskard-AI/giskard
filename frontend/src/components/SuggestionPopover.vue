<template>
  <v-menu offset-x :close-on-content-click="false" v-model="opened" v-if="val">
    <template v-slot:activator="{ on: onMenu }">
      <v-tooltip right>
        <template v-slot:activator='{ on: onTooltip }'>
          <v-btn small icon v-on="{ ...onMenu, ...onTooltip }" :disabled="props.disabled">
            <v-badge color="error" content="3" overlap>
              <v-icon size="18">mdi-auto-fix</v-icon>
            </v-badge>
          </v-btn>
        </template>
        <span>Suggestions</span>
      </v-tooltip>
    </template>


    <v-card dark color="primary">
      <v-card-title>
        <!--        Potential improvements for-->
        {{ value.pushTitle }}
      </v-card-title>
      <v-card-text>
        <v-list light two-line>
          <template v-for="detail in value.details">
            <v-list-item>
              <v-list-item-content>
                <v-list-item-title>
                  <!--                This value is responsible for the prediction being wrong.-->
                  {{ detail.action }}
                </v-list-item-title>
                <v-list-item-subtitle>
                  <!--                Open the inspector with similar examples ?-->
                  {{ detail.explanation }}
                </v-list-item-subtitle>
              </v-list-item-content>
              <v-list-item-action>
                <v-btn small text color="primary" @click.stop="dbg_GetSuggestion">
                  <!--                <v-icon>mdi-check</v-icon>-->
                  {{ detail.button }}
                </v-btn>
                <!--              <v-btn small icon color="error">-->
                <!--                <v-icon>mdi-close</v-icon>-->
                <!--              </v-btn>-->
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
import {api} from "@/api";
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
  await api.getSuggestions(props.modelId ?? "", props.datasetId ?? "", props.rowNb ?? 0);
}

const val = computed(() => {
  const list = pushStore.getPushSuggestions(props.modelId ?? "", props.datasetId ?? "", props.rowNb ?? 0);
  return list ? list.filter((s) => s.key == props.column)[0] : undefined;
});
</script>

<style scoped>

</style>