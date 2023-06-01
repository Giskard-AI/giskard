<template>
  <v-stepper v-model="step" flat>
    <v-stepper-header id="stepper-header">
      <v-stepper-step :complete="step > 1" step="1">Start ML Worker</v-stepper-step>
      <v-divider></v-divider>
      <v-stepper-step :complete="step > 2" step="2">Create Giskard client</v-stepper-step>
      <v-divider></v-divider>
      <v-stepper-step :complete="step > 3" step="3">Wrap Giskard artifacts</v-stepper-step>
      <v-divider></v-divider>
      <v-stepper-step step="4">Test your model</v-stepper-step>
    </v-stepper-header>

    <v-stepper-items>
      <v-stepper-content step="1">
        <div class="mb-6" v-if="externalWorker !== null">
          <p>ML Worker is already running!</p>
          <p>You can skip this step.</p>
        </div>
        <div class="mb-6" v-else>
          <StartWorkerInstructions></StartWorkerInstructions>
        </div>
        <v-btn color="primary" @click="step = 2">Continue</v-btn>
        <v-btn class="ml-2" @click="close" flat>Cancel</v-btn>
      </v-stepper-content>

      <v-stepper-content step="2">
        <div class="mb-6">
          <p class="mb-2">Create a Giskard client with the following Python code:</p>
          <CodeSnippet :codeContent="clientCodeContent"></CodeSnippet>
        </div>
        <v-btn color="primary" @click="step = 3">Continue</v-btn>
        <v-btn class="ml-2" @click="close" flat>Cancel</v-btn>
      </v-stepper-content>

      <v-stepper-content step="3">
        <div class="mb-6">
          <p class="mb-2">Choose the type of artifact you want to create:</p>
          <v-btn-toggle v-model="toggleArtifactType" borderless mandatory color="primary">
            <v-btn value="dataset" class="py-5 px-4">
              <span>Dataset</span>
            </v-btn>
            <v-btn value="model" class="py-5 px-4">
              <span>Model</span>
            </v-btn>
          </v-btn-toggle>
          <p class="mt-4 mb-2">Then, create the artifact with the following Python code:</p>
          <CodeSnippet v-show="toggleArtifactType === 'dataset'" :codeContent="datasetCodeContent"></CodeSnippet>
          <CodeSnippet v-show="toggleArtifactType === 'model'" :codeContent="modelCodeContent"></CodeSnippet>
        </div>
        <v-btn color="primary" @click="step = 4">Continue</v-btn>
        <v-btn class="ml-2" @click="close" flat>Cancel</v-btn>
      </v-stepper-content>

      <v-stepper-content step="4">
        <div class="mb-6">
          <p class="mb-2">Choose the type of test you want to perform:</p>
          <v-btn-toggle v-model="toggleTestType" borderless mandatory color="primary">
            <v-btn value="scan" class="py-5 px-4">
              <span>Automatic Scan</span>
            </v-btn>
            <v-btn value="manual" class="py-5 px-4">
              <span>Manual Testing</span>
            </v-btn>
          </v-btn-toggle>
          <p class="mt-4 mb-2">Then, run the following Python code:</p>
          <CodeSnippet v-show="toggleTestType === 'scan'" :codeContent="scanCodeContent"></CodeSnippet>
          <CodeSnippet v-show="toggleTestType === 'manual'" :codeContent="manualTestCodeContent"></CodeSnippet>
        </div>
        <v-btn color="primary" @click="close">Close</v-btn>
        <v-btn class="ml-2" @click="step = 1" flat>Restart</v-btn>
      </v-stepper-content>
    </v-stepper-items>
  </v-stepper>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { api } from "@/api";
import { apiURL } from "@/env";
import { MLWorkerInfoDTO, ProjectDTO } from "@/generated-sources";
import CodeSnippet from "./CodeSnippet.vue";
import StartWorkerInstructions from "./StartWorkerInstructions.vue";

interface Props {
  project: ProjectDTO;
}

const props = defineProps<Props>();

const step = ref<number>(1);
const toggleArtifactType = ref<string>("dataset");
const toggleTestType = ref<string>("scan");

const allMLWorkerSettings = ref<MLWorkerInfoDTO[]>([]);
const externalWorker = ref<MLWorkerInfoDTO | null>(null);

const apiAccessToken: string = "my_API_Access_Token";

const clientCodeContent = computed(() => {
  return `# Create a Giskard client
from giskard import GiskardClient
url = "${apiURL}" # URL of your Giskard instance
token = "${apiAccessToken}" # Your API Access Token (generate one in Settings > API Access Token > Generate)
client = GiskardClient(url, token)`
})

const datasetCodeContent = computed(() => {
  return `import pandas as pd

iris_df = pd.DataFrame({"sepal length": [5.1],
                        "sepal width": [3.5],
                        "petal size": ["medium"],
                        "species": ["Setosa"]})

from giskard import wrap_dataset

wrapped_dataset = wrap_dataset(
  df=iris_df, 
  target="species", # Optional but a MUST if available
  cat_columns=["petal size"] # Optional but a MUST if available. Inferred automatically if not.
  # name="my_iris_dataset", # Optional
  # column_types=None # # Optional: if not provided, it is inferred automatically
)
  
dataset_id = wrapped_dataset.upload(client, "${props.project.key}")`
})

const modelCodeContent = computed(() => {
  return `import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from giskard import wrap_model

scaler = StandardScaler()
clf = LogisticRegression()

def prediction_function(df: pd.DataFrame) -> np.ndarray:
  #Scale all the numerical variables
  num_cols = ["sepal length", "sepal width"]
  df[num_cols] = scaler.transform(df[num_cols])
  
  return clf.predict_proba(df)


wrapped_model = wrap_model(
  prediction_function,
  model_type="classification",
  classification_labels=['Setosa', 'Versicolor', 'Virginica'],
  feature_names=['sepal length', 'sepal width'],  # Default: all columns of your dataset
  # name="my_iris_classification_model", # Optional
  # classification_threshold=0.5, # Default: 0.5
)

model_id = wrapped_model.upload(client, "${props.project.key}")`
})

const scanCodeContent: string = `import giskard

results = giskard.scan(wrapped_model, wrapped_dataset)

display(results)  # in your notebook`;

const manualTestCodeContent = computed(() => {
  return `from giskard import Suite, test_f1, DataQuality

suite = Suite()
  .add_test(test_f1(actual_slice=wrapped_dataset))
  .add_test(DataQuality(dataset=wrapped_dataset, column_name='species', category='Setosa'))
  .save(client, "${props.project.key}")`
});

const emit = defineEmits(["close"]);

const close = () => {
  emit("close");
  step.value = 1;
}

onMounted(async () => {
  try {
    allMLWorkerSettings.value = await api.getMLWorkerSettings();
    externalWorker.value = allMLWorkerSettings.value.find(worker => worker.isRemote === true) || null;
  } catch (error) { }

  if (externalWorker.value) {
    step.value = 2;
  }
});
</script>

<style scoped>
#stepper-header {
  background-color: transparent;
  box-shadow: none !important;
}

.v-btn {
  margin-bottom: 0.5rem;
}
</style>