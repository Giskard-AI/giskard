<template>
  <div>
    <v-container class="mt-2 mb-0" v-if="isProjectOwnerOrAdmin">
      <div class="d-flex justify-end align-center">
        <v-btn @click="openCreateDialog" color="primary">
          Create
        </v-btn>
        <v-btn text @click="loadSlices()" color="secondary">Reload
          <v-icon right>refresh</v-icon>
        </v-btn>
      </div>
    </v-container>
    <v-container>
      <v-expansion-panels v-if="slices.length > 0">

        <v-row dense no-gutters class="mr-12 ml-2 caption secondary--text text--lighten-3 pb-2">
          <v-col cols="4">Name</v-col>
          <v-col cols="4">Created on</v-col>
          <v-col cols="3">Id</v-col>
          <v-col>Actions</v-col>
        </v-row>

        <v-expansion-panel v-for="slice in slices">
          <v-expansion-panel-header class="py-1 pl-2">
            <v-row dense no-gutters align="center">
              <v-col cols="4" class="font-weight-bold">{{ slice.name }}</v-col>
              <v-col cols="4">{{ slice.createdDate | date }}</v-col>
              <v-col cols="3"> {{ slice.id }}</v-col>
              <v-col>
                <span>
              <v-tooltip bottom dense>
                <template v-slot:activator="{ on, attrs }">
                    <v-btn icon color="accent" v-if="isProjectOwnerOrAdmin"
                           @click.stop="deleteSlice(slice.id)"
                           v-bind="attrs" v-on="on">
                      <v-icon>delete</v-icon>
                    </v-btn>
                  </template>
                <span>Delete</span>
              </v-tooltip>
            </span>
              </v-col>
            </v-row>

          </v-expansion-panel-header>
          <v-expansion-panel-content>
            <div> <!-- TODO: v-if slice comes from UI Editor... -->
              <MonacoEditor
                  v-model='slice.code'
                  language='python'
                  style="height: 100px"
                  :options="$root.monacoOptions"
              />
            </div>
          </v-expansion-panel-content>
        </v-expansion-panel>
      </v-expansion-panels>
      <span v-on:click="openCreateDialog" v-else>No slices created yet.</span>
    </v-container>

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
import * as monaco from 'monaco-editor';
import {editor} from 'monaco-editor';

import {onActivated, ref} from "vue";
import {api} from "@/api";
import {SliceDTO} from "@/generated-sources";

interface Props {
  projectId: number,
  isProjectOwnerOrAdmin: boolean
}

const props = defineProps<Props>()

const slices = ref<SliceDTO[]>([])
const sliceName = ref<string>("");
const sliceCode = ref<string>("def filter_row(row):\n    return True;");
const createDialog = ref<boolean>(false);

onActivated(() => {
  loadSlices();
})

async function createSlice() {
  const newSlice = await api.createSlice(props.projectId, sliceName.value, sliceCode.value);
  slices.value.push(newSlice);
  closeCreateDialog();
}

function deleteSlice(id: number) {
  // TODO: Api call
}

function openCreateDialog() {
  createDialog.value = true;
}

function closeCreateDialog() {
  createDialog.value = false;
  sliceName.value = "";
  sliceCode.value = "def filter_row(row):\n    return True;";
}

async function loadSlices() {
  slices.value = await api.getProjectSlices(props.projectId)
}

</script>

<style scoped>
.editor {
  height: 100%;
  border: 1px solid grey;

  ::v-deep .suggest-widget {
    display: none;
  }
}
</style>