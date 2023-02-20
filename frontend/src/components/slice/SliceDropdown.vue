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
        <template v-if="isProjectOwnerOrAdmin && !isCreateSlice(data.item.value)">
          <v-btn icon @click.stop="openEditDialog(data.item)">
            <v-icon>edit</v-icon>
          </v-btn>
          <v-btn icon @click.stop="deleteSlice(data.item)">
            <v-icon>delete</v-icon>
          </v-btn>
        </template>
      </template>
    </v-autocomplete>

    <v-dialog v-model="sliceDialog" width="800" persistent>
      <v-card>
        <ValidationObserver ref="dialogForm">
          <v-form @submit.prevent="submit()">
            <v-card-title v-if="isUpdateDialog">Editing slice</v-card-title>
            <v-card-title v-else>Creating new slice</v-card-title>
            <v-card-subtitle>{{ sliceName }}</v-card-subtitle>
            <v-card-text>
              <ValidationProvider name="Name" mode="eager" rules="required" v-slot="{errors}">
                <v-text-field label="Slice Name*" type="text" v-model="sliceName"
                              :rules="[rules.required, rules.counter]"
                              :error-messages="errors" :autofocus="!isUpdateDialog" counter="50"></v-text-field>
              </ValidationProvider>
              <span>Python function</span>
              <MonacoEditor
                  ref="editor"
                  v-model='sliceCode'
                  class='editor'
                  language='python'
                  style="height: 300px"
                  :options="editorOptions"
              />
            </v-card-text>
            <v-card-actions>
              <v-autocomplete label="Validate with" :items="datasets" item-text="name" item-value="id"
                              v-model="selectedDatasetId" style="max-width: 300px">
              </v-autocomplete>
              <v-tooltip bottom>
                <template v-slot:activator="{ on, attrs }">
                  <v-btn text v-on="on" v-bind="attrs" @click="validateCode" :disabled="selectedDatasetId === -1">
                    Validate
                  </v-btn>
                </template>
                <span>Runs the function on a few rows from the selected dataset to validate it.</span>
              </v-tooltip>
              <v-spacer></v-spacer>
              <v-btn color="error" text @click="closeSliceDialog()">Cancel</v-btn>
              <v-btn color="primary" text type="submit">
                <div v-if="isUpdateDialog">Update</div>
                <div v-else>Create</div>
              </v-btn>
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
import {computed, getCurrentInstance, onMounted, ref, watch} from "vue";
import {DatasetDTO, SliceDTO} from "@/generated-sources";
import {api} from "@/api";
import {editor} from "monaco-editor";
import {useMainStore} from "@/stores/main";
import mixpanel from "mixpanel-browser";
import IEditorOptions = editor.IEditorOptions;

const mainStore = useMainStore();

interface Props {
  projectId: number,
  loading?: boolean,
  create?: boolean,
  isProjectOwnerOrAdmin?: boolean,
  defaultDatasetId?: number
}

const props = defineProps<Props>();
const emit = defineEmits(["onSelect", "onClear"])

const slices = ref<SliceDTO[]>([])
const slice = ref<SliceDTO | null>(null);

const sliceDialog = ref<boolean>(false);
const sliceName = ref<string>("");
const sliceCode = ref<string>("");
const sliceId = ref<number>(-1);
const datasets = ref<DatasetDTO[]>([]);
const selectedDatasetId = ref<number>(-1);

const autocomplete = ref<any | null>(null);
const editor = ref<any | null>(null);

onMounted(() => {
  loadSlices();
  if (props.defaultDatasetId) {
    selectedDatasetId.value = props.defaultDatasetId;
  }
})


const editorOptions: IEditorOptions = {
  // @ts-ignore
  ...getCurrentInstance()?.proxy.$root.monacoOptions,
  minimap: {enabled: false},
  suggest: {preview: false}
}

const rules = {
  counter: (value) => value.length <= 50 || 'Max 50 characters',
  required: (value) => !!value || 'Required'
}

const exampleSliceCode: string = `
# Define a function 'filter_row' that will run over every single row of your dataset.
# This function should return a boolean if the row is part of your slice.
def filter_row(row):
    # For example, a dataset that contains a numeric column "age" could be filtered with the following expression:
    # return row['age'] > 60
    return True
`;

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

const isUpdateDialog = computed(() => {
  return sliceId.value >= 0
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

  await api.deleteSlice(props.projectId, sliceToDel.id);
  slices.value = slices.value.filter(s => s.id !== sliceToDel.id)
}

async function openCreateDialog() {
  sliceName.value = '';
  sliceCode.value = exampleSliceCode;
  sliceDialog.value = true;
  autocomplete.value.reset();
  datasets.value = await api.getProjectDatasets(props.projectId)
}

async function openEditDialog(value: SliceDTO) {
  sliceName.value = value.name;
  sliceCode.value = value.code;
  sliceId.value = value.id;
  sliceDialog.value = true;
  datasets.value = await api.getProjectDatasets(props.projectId)
}

function closeSliceDialog() {
  sliceId.value = -1;
  sliceDialog.value = false;
}

async function submit() {
  if (isUpdateDialog.value) {
    const editedSlice = await api.editSlice(props.projectId, sliceName.value, sliceCode.value, sliceId.value);
    slices.value = slices.value.filter(s => s.id !== editedSlice.id);
    slices.value.push(editedSlice);
    // This check is in place because we remove the original slice instance from the list.
    // This also triggers a change, which is helpful if the code changed.
    if (slice.value?.id == editedSlice.id) {
      slice.value = editedSlice;
    }
  } else {
    const newSlice = await api.createSlice(props.projectId, sliceName.value, sliceCode.value);
    slices.value.push(newSlice);
    slice.value = newSlice;
    mixpanel.track('Create slice', {sliceName: newSlice.name, sliceId: newSlice.id});
  }

  closeSliceDialog();
}

async function validateCode() {
  await api.validateSlice(selectedDatasetId.value, sliceCode.value);
  await mainStore.addNotification({content: "Slice code is valid", color: "success"})
}
</script>

<style>
.monaco-editor .suggest-widget {
  display: none !important;
  visibility: hidden !important;
}
</style>