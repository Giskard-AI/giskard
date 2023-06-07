<template>
  <v-stepper v-model="step" flat>
    <v-stepper-header id="stepper-header">
      <v-stepper-step :complete="step > 1" step="1">Start ML Worker</v-stepper-step>
      <v-divider></v-divider>
      <v-stepper-step :complete="step > 2" step="2">Upload your dataset and model</v-stepper-step>
      <v-divider></v-divider>
      <v-stepper-step step="3">Test your model</v-stepper-step>
    </v-stepper-header>

    <v-stepper-items>
      <v-stepper-content step="1" class="stepper-content">
        <div class="mb-6" v-if="externalWorker !== null">
          <p>ML Worker is already running!</p>
          <p>You can skip this step.</p>
        </div>
        <div class="mb-6" v-else>
          <StartWorkerInstructions></StartWorkerInstructions>
        </div>
        <div class="d-flex">
          <v-btn color="primary" @click="step++">Continue</v-btn>
          <v-spacer></v-spacer>
          <v-btn @click="close" text>Cancel</v-btn>
        </div>
      </v-stepper-content>
      <v-stepper-content step="2" class="stepper-content">
        <div class="mb-6">
          <div v-if="apiAccessToken && apiAccessToken.id_token">
            <CodeSnippet :codeContent='uploadSnippet'></CodeSnippet>
          </div>
        </div>
        <div class="d-flex">
          <v-btn color="primary" @click="step++">Continue</v-btn>
          <v-btn color="ml-2" @click="step--">Back</v-btn>
          <v-spacer></v-spacer>
          <v-btn @click="close" text>Cancel</v-btn>
        </div>
      </v-stepper-content>

      <v-stepper-content step="3" class="stepper-content">
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
          <v-btn color="ml-2" @click="step--">Back</v-btn>
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
import { JWTToken, MLWorkerInfoDTO, ProjectDTO } from "@/generated-sources";
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


const uploadSnippet = computed(() => {
  // language=Python
  return `from giskard import Dataset, Model, GiskardClient
from giskard.demo import titanic  # for demo purposes only 🛳️

original_model, original_df = titanic()  # Replace with your dataframe creation

# Create a Giskard client
token = "${apiAccessToken.value!.id_token}"
client = GiskardClient(
    url="${apiURL}",  # URL of your Giskard instance
    token=token
)

# Wrap your Pandas Dataframe and model with Giskard 🎁
giskard_dataset = Dataset(original_df, target="Survived", name="Titanic dataset")
giskard_model = Model(original_model, model_type="classification", name="Titanic model")

# Upload to the current project ✉️
giskard_dataset.upload(client, "${props.project.key}")
giskard_model.upload(client, "${props.project.key}")`
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
  // language=Python
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

results = giskard.scan(giskard_model, giskard_dataset)

# Show results in your notebook
# display(results)

# Upload an automatically created test suite
results.generate_test_suite("Test suite created by scan").upload(client, "${props.project.key}")`;

const manualTestCodeContent = computed(() => {
  // language=Python
  return `from giskard import Suite
from giskard.testing.tests.performance import test_f1

suite = Suite() \\
    .add_test(test_f1(dataset=giskard_dataset))

suite.run(model=giskard_model)
`
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