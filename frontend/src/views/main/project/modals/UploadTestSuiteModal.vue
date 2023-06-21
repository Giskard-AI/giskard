<template>
  <vue-final-modal v-slot="{ close }" v-bind="$attrs" classes="modal-container" content-class="modal-content" v-on="$listeners">
    <div>
      <v-card>
        <v-card-title>
          Upload a test suite
          <v-spacer></v-spacer>
          <v-btn text href="https://docs.giskard.ai/en/latest/guides/test-suite/index.html" target="_blank" rel="noopener">
            <span>Documentation</span>
            <v-icon right>mdi-open-in-new</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-text>
          <p class="mb-2">Choose the type of test you want to perform:</p>
          <v-btn-toggle v-model="toggleTestType" borderless mandatory color="primary">
            <v-btn value="scan" class="py-5 px-4">
              <span>Automatic Scan</span>
            </v-btn>
            <v-btn value="manual" class="py-5 px-4">
              <span>Manual Testing</span>
            </v-btn>
          </v-btn-toggle>
          <div v-show="toggleTestType === 'scan'">
            <p class="mt-4 mb-4">To scan your model, run the following Python code:</p>
            <CodeSnippet :codeContent="scanCodeContent"></CodeSnippet>
            <p class="mt-4 mb-0">Check out the <a href="https://docs.giskard.ai/en/latest/guides/scan/index.html" target="_blank" rel="noopener" class="font-weight-bold text-body-1 mx-1">scan documentation</a> for more information and examples.</p>
          </div>
          <div v-show="toggleTestType === 'manual'">
            <p class="mt-4 mb-4">To manually test your model, run the following Python code:</p>
            <CodeSnippet :codeContent="manualTestCodeContent"></CodeSnippet>
            <p class="mt-4 mb-0">Check out the <a href="https://docs.giskard.ai/en/latest/guides/test-suite/index.html" target="_blank" rel="noopener" class="font-weight-bold text-body-1 mx-1">test suite documentation</a> for more information and examples.</p>
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
import { ref, computed } from "vue";
import { JWTToken } from "@/generated-sources";
import CodeSnippet from "@/components/CodeSnippet.vue";

interface Props {
  apiAccessToken: JWTToken,
  projectKey: string,
}

const props = defineProps<Props>();

const toggleTestType = ref<string>("scan");

const scanCodeContent = computed(() => {
  return `import giskard

results = giskard.scan(giskard_model, giskard_dataset)

# Show results in your notebook
# display(results)

# Upload an automatically created test suite
results.generate_test_suite("Test suite created by scan").upload(client, "${props.projectKey}")`
});

const manualTestCodeContent = computed(() => {
  return `from giskard import Suite
from giskard.testing.tests.performance import test_f1

suite = Suite().add_test(test_f1(dataset=giskard_dataset))

suite.run(model=giskard_model)
`
});
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