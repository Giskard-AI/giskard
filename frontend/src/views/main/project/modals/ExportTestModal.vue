<template>
  <vue-final-modal v-slot="{ close }" v-bind="$attrs" classes="modal-container" content-class="modal-content" v-on="$listeners">
    <div>
      <v-card>
        <v-card-title>
          Export Test Suite
          <v-spacer></v-spacer>
          <v-btn text href="https://docs.giskard.ai/en/latest/" target="_blank">
            <span>Documentation</span>
            <v-icon right>mdi-open-in-new</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-text>
          <div id="export-default">
            <p>Export to a Python notebook</p>
            <CodeSnippet :key="codeContent" :codeContent="codeContent" :language="'python'"></CodeSnippet>
          </div>
          <div v-show="false">
            <p>Export to a CI pipeline</p>
            <CodeSnippet :codeContent="codeContent" :language="'python'"></CodeSnippet>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text class="mr-2 mb-2" color="primary" @click="close">Close</v-btn>
        </v-card-actions>
      </v-card>
    </div>
  </vue-final-modal>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue';
import { useProjectStore } from '@/stores/project';
import CodeSnippet from '@/components/CodeSnippet.vue';
import { generateGiskardClientSnippet } from '@/snippets';

interface Props {
  projectId: number;
  suiteId: number;
}

const props = defineProps<Props>();

const projectStore = useProjectStore();

const giskardClientSnippet = ref<string | null>(null);

const project = computed(() => projectStore.project(props.projectId))

const codeContent = computed(() => {
  let content = `import giskard\n`;
  content += `${giskardClientSnippet.value}\n`;
  content += `# Load test suite from Giskard Hub\n`;
  content += `my_test_suite = giskard.Suite.download(client, "${project.value!.key}", ${props.suiteId})`;
  return content;
});

onMounted(async () => {
  giskardClientSnippet.value = await generateGiskardClientSnippet();
})
</script>

<style scoped>
::v-deep(.modal-container) {
  height: 100%;
  padding: 0;
  margin: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow-y: auto;
}

::v-deep(.modal-content) {
  width: 80vw;
  height: fit-content;
}
</style>