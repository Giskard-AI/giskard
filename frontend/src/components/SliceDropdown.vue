<template>
  <div>
    <v-autocomplete label="Slice to apply"
                    :items="items"
                    v-model="slice"
                    placeholder="Select a slice..."
                    :loading="loading"
                    clearable
                    ref="autocomplete">
      <template v-slot:item="data">
        {{ data.item.text }}
        <v-spacer/>
        <v-btn icon color="error" v-if="isProjectOwnerOrAdmin && !isCreateSlice(data.item.value)"
               @click.stop="deleteSlice(data.item)">
          <v-icon>delete</v-icon>
        </v-btn>
      </template>
    </v-autocomplete>
    <v-dialog v-model="createDialog" width="800" persistent>
      <v-card>
        <ValidationObserver ref="dialogForm">
          <v-form @submit.prevent="createSlice()">
            <v-card-title>Create new slice</v-card-title>
            <v-card-text>
              <ValidationProvider name="Name" mode="eager" rules="required" v-slot="{errors}">
                <v-text-field label="Slice Name*" type="text" v-model="sliceName"
                              :error-messages="errors"></v-text-field>
              </ValidationProvider>
              <span>Python function</span>
              <MonacoEditor
                  ref="editor"
                  v-model='sliceCode'
                  class='editor'
                  language='python'
                  style="height: 300px"
                  :options="$root.monacoOptions"
              />
              <!--              <div v-if="projectCreateError" class="caption error&#45;&#45;text">{{ projectCreateError }}</div>-->
            </v-card-text>
            <v-card-actions>
              <v-spacer></v-spacer>
              <v-btn color="error" text @click="closeCreateDialog()">Cancel</v-btn>
              <v-btn color="secondary" text>Validate</v-btn>
              <v-btn color="primary" text type="submit">Create</v-btn>
            </v-card-actions>
          </v-form>
        </ValidationObserver>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
// @ts-ignore
import MonacoEditor from 'vue-monaco';
import {computed, onMounted, ref, watch} from "vue";
import {SliceDTO} from "@/generated-sources";
import {api} from "@/api";

interface Props {
  projectId: number,
  loading?: boolean,
  create?: boolean,
  isProjectOwnerOrAdmin?: boolean
}

const props = defineProps<Props>();
const emit = defineEmits(["onSelect", "onClear"])

const slices = ref<SliceDTO[]>([])
const slice = ref<SliceDTO | null>(null);

const createDialog = ref<boolean>(false);
const sliceName = ref<string>("");
const sliceCode = ref<string>("");

const autocomplete = ref<any | null>(null);

onMounted(() => {
  loadSlices();
})

const items = computed(() => {
  // TODO: Find a solution for this typing issue
  let result: any[] = slices.value.map(slice => ({
    ...slice,
    text: slice.name,
    value: slice
  }));

  if (props.isProjectOwnerOrAdmin) {
    result.push({text: "Create new slice...", value: "__NEW_SLICE__", name: "__NEW_SLICE__"})
  }
  
  return result;
})

watch(() => slice.value, (value, oldValue) => {
  if (value !== null) {
    if (isCreateSlice(value)) {
      openCreateDialog();
    } else {
      emit('onSelect', value);
    }
  } else if (!isCreateSlice(oldValue)) {
    emit('onClear');
  }
})

async function loadSlices() {
  slices.value = await api.getProjectSlices(props.projectId)
}

function isCreateSlice(value): boolean {
  return value === "__NEW_SLICE__";
}

async function deleteSlice(sliceToDel: SliceDTO) {
  if (sliceToDel === slice.value) {
    autocomplete.value.reset();
  }

  await api.deleteSlice(sliceToDel.id);
  slices.value = slices.value.filter(s => s.id !== sliceToDel.id)
}

function openCreateDialog() {
  sliceName.value = '';
  sliceCode.value = 'def filter_row(row):\n    return True';
  createDialog.value = true;
  autocomplete.value.reset();
}

function closeCreateDialog() {
  createDialog.value = false;
}

async function createSlice() {
  const newSlice = await api.createSlice(props.projectId, sliceName.value, sliceCode.value);
  slices.value.push(newSlice);
  closeCreateDialog();
  slice.value = newSlice;
}
</script>

<style scoped>

</style>