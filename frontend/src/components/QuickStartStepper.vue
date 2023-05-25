<template>
  <v-stepper v-model="step" flat>
    <v-stepper-header id="stepper-header">
      <v-stepper-step :complete="step > 1" step="1">Start ML Worker</v-stepper-step>
      <v-divider></v-divider>
      <v-stepper-step :complete="step > 2" step="2">Create Giskard client</v-stepper-step>
      <v-divider></v-divider>
      <v-stepper-step :complete="step > 3" step="3">Upload Giskard artifacts</v-stepper-step>
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
        <div class="d-flex">
          <v-btn color="primary" @click="step = 2">Continue</v-btn>
          <v-spacer></v-spacer>
          <v-btn @click="close" text>Cancel</v-btn>
        </div>
      </v-stepper-content>

      <v-stepper-content step="2">
        <div class="mb-6">
          <p class="mb-2">First, you must have access to an API Access Token.</p>
          <div v-if="apiAccessToken && apiAccessToken.id_token">
            <CodeSnippet :codeContent='`token = "${apiAccessToken.id_token}" # Your API Access Token`'></CodeSnippet>
          </div>
          <div v-else>
            <p>If you don't have one, you can click on the button below.</p>
            <v-btn color="primaryLight" class="primaryLightBtn" @click="generateApiAccessToken">Generate</v-btn>
          </div>
          <p class="my-2">Then, create a Giskard client with the following Python code:</p>
          <CodeSnippet :codeContent="clientCodeContent"></CodeSnippet>
        </div>
        <div class="d-flex">
          <v-btn color="primary" @click="step = 3">Continue</v-btn>
          <v-btn color="ml-2" @click="step = 1">Back</v-btn>
          <v-spacer></v-spacer>
          <v-btn @click="close" text>Cancel</v-btn>
        </div>
      </v-stepper-content>

      <v-stepper-content step="3" class="pl-0">
        <p class="mb-2 ml-6">You can wrap your artifacts in two ways:</p>
        <v-stepper vertical flat v-model="artifactsStep">
          <v-stepper-step :complete="artifactsStep > 1" step="1" color="secondary">
            Upload a dataset
          </v-stepper-step>
          <v-stepper-content step="1">
            <CodeSnippet :codeContent="datasetCodeContent"></CodeSnippet>
          </v-stepper-content>

          <v-stepper-step :complete="artifactsStep > 2" step="2" color="secondary">
            Upload a model
          </v-stepper-step>
          <v-stepper-content step="2">
            <CodeSnippet :codeContent="modelCodeContent"></CodeSnippet>
          </v-stepper-content>
        </v-stepper>

        <div class="d-flex">
          <v-btn color="primary" class="ml-6" @click="() => {
            if (artifactsStep === 1) {
              artifactsStep = 2
            } else {
              step = 4
              artifactsStep = 1
            }
          }">Continue</v-btn>
          <v-btn color="ml-2" @click="() => {
            if (artifactsStep === 1) {
              step = 2
            } else {
              artifactsStep = 1
            }
          }">Back</v-btn>
          <v-spacer></v-spacer>
          <v-btn @click="close" text>Cancel</v-btn>
        </div>
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
          <div v-show="toggleTestType === 'scan'">
            <p class="mt-4 mb-2">To scan your model, run the following Python code:</p>
            <CodeSnippet :codeContent="scanCodeContent"></CodeSnippet>
          </div>
          <div v-show="toggleTestType === 'manual'">
            <p class="mt-4 mb-2">To manually test your model, run the following Python code:</p>
            <CodeSnippet :codeContent="manualTestCodeContent"></CodeSnippet>
          </div>
        </div>
        <div class="d-flex">
          <v-btn color="primary" @click="close">Close</v-btn>
          <v-btn color="ml-2" @click="step = 3">Back</v-btn>
          <v-spacer></v-spacer>
          <v-btn class="ml-2" @click="step = 1; artifactsStep = 1" text>Restart</v-btn>
        </div>
      </v-stepper-content>
    </v-stepper-items>
  </v-stepper>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { api } from "@/api";
import { apiURL } from "@/env";
import { MLWorkerInfoDTO, ProjectDTO, JWTToken } from "@/generated-sources";
import CodeSnippet from "./CodeSnippet.vue";
import StartWorkerInstructions from "./StartWorkerInstructions.vue";

interface Props {
  project: ProjectDTO;
}

const props = defineProps<Props>();

const step = ref<number>(1);
const artifactsStep = ref<number>(1);
const toggleTestType = ref<string>("scan");
const apiAccessToken = ref<JWTToken | null>(null);
const allMLWorkerSettings = ref<MLWorkerInfoDTO[]>([]);
const externalWorker = ref<MLWorkerInfoDTO | null>(null);

const clientCodeContent = computed(() => {
  return `from giskard import GiskardClient

url = "${apiURL}" # URL of your Giskard instance
client = GiskardClient(url, token)`
});

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

const generateApiAccessToken = async () => {
  try {
    apiAccessToken.value = await api.getApiAccessToken();
  } catch (error) {
    console.log(error);
  }
}

onMounted(async () => {
  try {
    allMLWorkerSettings.value = await api.getMLWorkerSettings();
    externalWorker.value = allMLWorkerSettings.value.find(worker => worker.isRemote === true) || null;
  } catch (error) { }

  await generateApiAccessToken();

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