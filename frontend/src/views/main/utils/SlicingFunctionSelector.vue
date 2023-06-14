<template>
    <div class="d-flex" :class="{ w100: fullWidth }">
      <v-select clearable :outlined='fullWidth' class='slice-function-selector' :label='label' v-model='value'
                :items="[{
            name: 'None',
            displayName: 'None',
            uuid: null,
            args: []
        }, ...availableSlicingFunctions]" :item-text='extractName' item-value='uuid' :return-object='false'
                @input='onInput'
                :dense='fullWidth' hide-details :prepend-inner-icon="icon ? 'mdi-knife' : null">
        <template v-slot:append-item v-if='allowNoCodeSlicing'>
          <v-list-item @click='createSlice'>
            <v-list-item-content>
              <v-list-item-title>
                <v-icon>add</v-icon>
                Create new slice
              </v-list-item-title>
            </v-list-item-content>
          </v-list-item>
        </template>
      </v-select>
        <v-btn icon v-if="hasArguments" @click="updateArgs">
            <v-icon>settings</v-icon>
        </v-btn>
    </div>
</template>

<script setup lang="ts">


import { DatasetDTO, FunctionInputDTO, SlicingFunctionDTO } from '@/generated-sources';
import { storeToRefs } from 'pinia';
import { useCatalogStore } from '@/stores/catalog';
import { computed } from 'vue';
import { $vfm } from 'vue-final-modal';
import FunctionInputsModal from '@/views/main/project/modals/FunctionInputsModal.vue';
import { chain } from 'lodash';
import CreateSliceModal from '@/views/main/project/modals/CreateSliceModal.vue';
import { DatasetProcessFunctionUtils } from '@/utils/dataset-process-function.utils';

const props = withDefaults(defineProps<{
  projectId: number,
  label: string,
  fullWidth: boolean,
  value?: string,
  args?: Array<FunctionInputDTO>,
  icon: boolean,
  dataset?: DatasetDTO,
  allowNoCodeSlicing: boolean
}>(), {
  fullWidth: true,
  icon: false,
  allowNoCodeSlicing: false
});

const emit = defineEmits(['update:value', 'update:args', 'onChanged']);

const { slicingFunctions, slicingFunctionsByUuid } = storeToRefs(useCatalogStore());

const availableSlicingFunctions = computed(() => props.dataset
  ? slicingFunctions.value.filter(slicingFn => DatasetProcessFunctionUtils.canApply(slicingFn, props.dataset!))
  : slicingFunctions.value);

function extractName(SlicingFunctionDTO: SlicingFunctionDTO) {
  return SlicingFunctionDTO.displayName ?? SlicingFunctionDTO.name;
}

async function onInput(value) {
  if (!value || slicingFunctionsByUuid.value[value].args.length === 0) {
    emit('update:value', value);
    emit('update:args', []);
    emit('onChanged');
    return;
  }

  const previousValue = props.value;
  emit('update:value', value);

  const func = slicingFunctionsByUuid.value[value];
  await $vfm.show({
    component: FunctionInputsModal,
    bind: {
      projectId: props.projectId,
      title: `Set up parameters for '${func.displayName ?? func.name}'`,
      function: func,
      defaultValue: {},
    },
    on: {
      async save(args: Array<FunctionInputDTO>) {
        emit('update:args', args);
        emit('onChanged');
      },
      async cancel() {
        // Rollback changes
        emit('update:value', previousValue)
      }
    },
    cancel: {}
  });
}

async function updateArgs() {
    const func = slicingFunctionsByUuid.value[props.value!];
    await $vfm.show({
        component: FunctionInputsModal,
        bind: {
            projectId: props.projectId,
            title: `Update parameters for '${func.displayName ?? func.name}'`,
            function: func,
            defaultValue: chain(props.args).keyBy('name').value(),
        },
        on: {
            async save(args: Array<FunctionInputDTO>) {
                emit('update:args', args);
                emit('onChanged');
            }
        },
        cancel: {}
    });
}

async function createSlice() {
    await $vfm.show({
        component: CreateSliceModal,
        bind: {
            dataset: props.dataset
        },
        on: {
            async created(uuid: string) {
                await onInput(uuid);
            }
        },
    })
}

const hasArguments = computed(() => props.value && props.value !== "None" && slicingFunctionsByUuid.value[props.value].args.length > 0)

</script>

<style scoped>
.slice-function-selector {
    min-width: 200px;
    flex-grow: 1;
}
</style>
