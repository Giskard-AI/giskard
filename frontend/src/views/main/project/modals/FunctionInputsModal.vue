<template>
  <vue-final-modal
      v-slot="{ close }"
      classes="modal-container"
      content-class="modal-content"
      v-bind="$attrs"
      v-on="$listeners"
      @click-outside="() => cancel()"
  >
    <v-form @submit.prevent="">
      <v-card class="modal-card">
        <v-card-title>
          {{ title }}
        </v-card-title>
        <v-card-text>
          <SuiteInputListSelector
              :editing="true"
              :inputs="inputs"
              :model-value="functionInputs"
              :project-id="projectId"
              class="pt-4"/>
        </v-card-text>

        <v-divider></v-divider>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
              color="secondary"
              text
              @click="cancel(close)"
          >
            Cancel
          </v-btn>
          <v-btn
              :disabled="invalid"
              color="primary"
              text
              @click="save(close)"
          >
            Save
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-form>
  </vue-final-modal>
</template>

<script lang="ts" setup>

import {computed, onMounted, ref} from 'vue';
import {CallableDTO, DatasetProcessFunctionDTO, FunctionInputDTO} from '@/generated-sources';
import SuiteInputListSelector from '@/components/SuiteInputListSelector.vue';
import {useMainStore} from "@/stores/main";

const props = defineProps<{
  projectId: number,
  title: string,
  function: CallableDTO,
  defaultValue: { [name: string]: Array<FunctionInputDTO> },
}>();

const functionInputs = ref<{ [name: string]: FunctionInputDTO }>({});
const inputs = ref<{ [name: string]: string }>({});

onMounted(() => loadData());

const emits = defineEmits(['save', 'cancel'])


async function loadData() {
  functionInputs.value = props.function.args?.reduce((result, arg) => {
    result[arg.name] = props.defaultValue[arg.name] ?? {
      name: arg.name,
      type: arg.type,
      isAlias: false,
      value: '',
      params: []
    }
    return result
  }, {} as { [name: string]: FunctionInputDTO }) ?? {};

  let processFunction = props.function as DatasetProcessFunctionDTO;
  if (processFunction.cellLevel) {
    functionInputs.value = {
      ...functionInputs.value,
      column_name: {
        type: 'str',
        value: null,
        isAlias: false,
        name: 'column_name',
        params: []
      }
    }
  }

  inputs.value = Object.entries(functionInputs.value)
      .reduce((result, [key, value]) => {
        result[key] = value
        return result
      }, {})
}


const invalid = computed(() => Object.values(functionInputs.value)
    .findIndex(param => param.value === null || param.value.trim() === '') !== -1)

const mainStore = useMainStore();

async function save(close) {
  emits('save', Object.values(functionInputs.value))
  close();
}

async function cancel(close?) {
  emits('cancel', props.defaultValue)
  if (close) {
    close();
  }
}

</script>

<style scoped>
::v-deep(.modal-container) {
  display: flex;
  justify-content: center;
  align-items: center;
}

::v-deep(.modal-content) {
  position: relative;
  display: flex;
  flex-direction: column;
  margin: 0 1rem;
  padding: 1rem;
}

.modal-card {
  min-width: 50vw;
}
</style>
