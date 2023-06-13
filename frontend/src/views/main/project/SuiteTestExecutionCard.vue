<template>
    <div class="test-container">
        <div class="d-flex flex-row flex-wrap align-center test-card-header">
            <span class="test-name text-black">
                Test {{ suiteTest.test.displayName ?? suiteTest.test.name }}
                <span v-if="transformationFunction"> to {{
                    transformationFunction.displayName ?? transformationFunction.name
                  }}</span>
                <span v-if="slicingFunction"> on slice {{ slicingFunction.displayName ?? slicingFunction.name }}</span>
            </span>
          <!-- TODO: Add tag to the test suite level (https://github.com/Giskard-AI/giskard/issues/1034)
              <div class="d-flex flex-row gap-4">
                  <v-chip v-if="!compact" v-for="tag in sorted(suiteTest.test.tags)" x-small :color="pasterColor(tag)"
                          label>
                      {{ tag }}
                  </v-chip>
              </div>
          -->
          <div class="flex-grow-1" />
            <div v-if="result" :class="`d-flex flex-row align-center gap-8 ${result.passed ? 'test-passed' : 'test-failed'}`">
                <span v-if="result.metric" class="metric">Measured <strong>Metric = {{
                    result.metric
                }}</strong></span>
                <v-chip v-if="result.passed" :color="Colors.PASS_SURFACE" :text-color="Colors.ON_PASS_SURFACE" label>
                    <v-icon>done</v-icon>
                    Passed
                </v-chip>
                <v-chip v-else small :color="Colors.FAIL_SURFACE" :text-color="Colors.ON_FAIL_SURFACE" label>
                    <v-icon small>close</v-icon>
                    Failed
                </v-chip>
                <v-tooltip bottom>
                    <template v-slot:activator="{ on, attrs }">
                        <div v-on="on">
                          <v-btn color="primary" outlined small disabled>
                            <v-icon small>info</v-icon>
                            Debug
                          </v-btn>
                        </div>
                    </template>
                  <span>Coming soon</span>
                </v-tooltip>
            </div>
        </div>
      <div class="d-flex flex-row flex-wrap align-end test-card-footer">
        <div v-for="({ name, value, type }) in orderedParams" class="d-flex flex-column">
          <span class="text-input-name">{{ name }}</span>
          <span :class="['BaseModel', 'Dataset'].includes(type) ? 'text-input-value' : 'text-input-value-code'">{{
              value
            }}</span>
        </div>
        <div class="flex-grow-1"/>
        <v-btn v-if="!isPastExecution" text small @click="editTests" color="rgba(0, 0, 0, 0.6)">
          <v-icon small class="mr-1">settings</v-icon>
          Edit parameters
        </v-btn>
      </div>
    </div>
</template>

<script setup lang="ts">

import {SuiteTestDTO, SuiteTestExecutionDTO} from '@/generated-sources';
import {computed} from "vue";
import {storeToRefs} from "pinia";
import {useCatalogStore} from "@/stores/catalog";
import {Colors} from "@/utils/colors";
import {$vfm} from "vue-final-modal";
import SuiteTestInfoModal from "@/views/main/project/modals/SuiteTestInfoModal.vue";
import {useTestSuiteStore} from "@/stores/test-suite";

const {slicingFunctionsByUuid, transformationFunctionsByUuid} = storeToRefs(useCatalogStore())
const {models, datasets} = storeToRefs(useTestSuiteStore())

const props = defineProps<{
  suiteTest: SuiteTestDTO,
  result?: SuiteTestExecutionDTO,
  compact: boolean,
    isPastExecution: boolean
}>();

const params = computed(() => props.isPastExecution && props.result
    ? props.result?.inputs
    : Object.values(props.suiteTest.functionInputs)
        .filter(input => !input.isAlias)
        .reduce((r, input) => ({ ...r, [input.name]: input.value }), {}))

function mapValue(value: string, type: string): string {
    if (type === 'SlicingFunction') {
        const slicingFunction = slicingFunctionsByUuid.value[value];
        return slicingFunction?.displayName ?? slicingFunction?.name ?? value
    } else if (type === 'TransformationFunction') {
        const transformationFunction = transformationFunctionsByUuid.value[value];
        return transformationFunction?.displayName ?? transformationFunction?.name ?? value
    } else if (type === 'BaseModel') {
        const model = models.value[value]
        return model.name ?? value
    } else if (type === 'Dataset') {
        const dataset = datasets.value[value]
        return dataset.name ?? value
    }
    return value;
}

const orderedParams = computed(() => params.value ? props.suiteTest.test.args
    .filter(({ name }) => params.value!.hasOwnProperty(name))
    .map(({ name, type }) => ({
        name: name.split('_').map(word => word[0].toUpperCase() + word.slice(1)).join(' '),
        value: mapValue(params.value[name], type),
        type
    }))
    : [])

const slicingFunction = computed(() => {
    const uuid = params.value ? params.value['slicing_function'] : undefined;

    if (uuid) {
        return slicingFunctionsByUuid.value[uuid];
    } else {
        return undefined;
    }
})

const transformationFunction = computed(() => {
    const uuid = params.value ? params.value['transformation_function'] : undefined;

    if (uuid) {
        return transformationFunctionsByUuid.value[uuid];
    } else {
        return undefined;
    }
})


async function editTests() {
    await $vfm.show({
        component: SuiteTestInfoModal,
        bind: {
            suiteTest: props.suiteTest
        }
    });
}
</script>

<style scoped lang="scss">
.test-container {
    border-radius: 4px 4px 4px 4px;
    -webkit-border-radius: 4px 4px 4px 4px;
    -moz-border-radius: 4px 4px 4px 4px;
    border: 1px solid rgb(224, 224, 224);
    background: white;
}

.test-card-header {
    padding: 10px;
    gap: 20px;
}

.test-card-footer {
    border-top: 1px solid #dee2e6;
    padding: 10px;
    gap: 20px;
}


.test-name {
    font-style: normal;
    font-weight: 500;
    font-size: 1em;
    line-height: 20px;
    letter-spacing: 0.0025em;
    color: #000000;
}

.gap-4 {
    gap: 8px;
}

.gap-8 {
    gap: 8px;
}

.metric {
    font-style: normal;
    font-weight: 400;
    font-size: 0.875em;
    line-height: 16px;
    letter-spacing: 0.0025em;
}

.test-failed {
    .metric {
        color: #B71C1C;
    }
}

.text-input-name {
    font-style: normal;
    font-weight: 400;
    font-size: 0.875em;
    line-height: 12px;
    letter-spacing: 0.0025em;
}

.text-input-value {
    font-style: normal;
    font-weight: 400;
    font-size: 0.875em;
    line-height: 24px;
    font-feature-settings: 'liga' off;
    color: #000000;
}

.text-input-value-code {
    font-family: 'Fira Code', "Helvetica Neue", sans-serif;
    font-style: normal;
    font-weight: 400;
    font-size: 0.75em;
    line-height: 24px;
    font-feature-settings: 'liga' off;
    color: #000000;
}
</style>

