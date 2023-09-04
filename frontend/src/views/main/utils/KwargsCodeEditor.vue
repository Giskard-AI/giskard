<template>
    <div class="mt-1 editor-container">
        <MonacoEditor ref="editor" :value="monacoValue" @change="onInput" class='editor' language='python' style="height: 150px" :options="monacoOptions" />
    </div>
</template>

<script setup lang="ts">

// import MonacoEditor from 'vue-monaco';
import { computed, inject, nextTick, onMounted, ref } from "vue";
import { editor } from "monaco-editor";
import IEditorOptions = editor.IEditorOptions;

// const l = MonacoEditor;
// const monacoOptions: IEditorOptions = inject('monacoOptions');
// monacoOptions.readOnly = false;

interface Props {
    value?: string | null;
}

const props = withDefaults(defineProps<Props>(), {
    value: undefined,
});

const monacoValue = computed(() => props.value ?? '');

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

<style scoped lang="scss">
.editor-container {
    border: 1px solid rgba(0, 0, 0, 0.4);
    border-radius: 5px;
    padding-top: 0.5rem;
    padding-bottom: 0.5rem;
}

.editor-container:hover {
    border: 1px solid rgba(0, 0, 0, 0.8);
}

.editor-container:focus-within {
    border: 2px solid #087038;
    padding-right: 1rem;
}

.editor {
    margin-right: 0.125rem;
}

.editor:focus {
    outline: none;
    margin-right: 0.125rem;
}

.v-card {
    border: 1px solid rgba(0, 0, 0, 0.4);
    border-radius: 5px;
}
</style>

