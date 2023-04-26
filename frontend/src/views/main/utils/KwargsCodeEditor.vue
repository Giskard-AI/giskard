<template>
    <MonacoEditor
        ref="editor"
        :value="props.value"
        @change="onInput"
        class='editor'
        language='python'
        style="height: 300px"
        :options="monacoOptions"
    />
</template>

<script setup lang="ts">

import MonacoEditor from 'vue-monaco';
import {inject, nextTick, onMounted, ref} from "vue";
import {editor} from "monaco-editor";
import IEditorOptions = editor.IEditorOptions;

const l = MonacoEditor;
const monacoOptions: IEditorOptions = inject('monacoOptions');
monacoOptions.readOnly = false;

const props = defineProps<{
    value?: string
}>()

const emit = defineEmits(['update:value']);

const editor = ref<any | null>(null);

onMounted(() => {
    if (!props.value) {
        emit('update:value', "# You can directly assign your arguments to the kwargs dictionary:\n# kwargs['example'] = ['example', 'value']\n")
    }
    nextTick(resizeEditor)
})

function resizeEditor() {
    setTimeout(() => {
        editor.value.editor.layout();
    })
}

function onInput(value: string) {
    console.log(value)
    emit('update:value', value)
}


</script>

