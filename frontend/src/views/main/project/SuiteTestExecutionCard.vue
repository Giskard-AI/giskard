<template>
    <div class="test-container">
        <div class="d-flex flex-row align-center test-card-header">
            <span class="test-name text-black">
                Test {{ suiteTest.test.displayName ?? suiteTest.test.name }}
                           <span v-if="transformationFunction"> to {{
                                   transformationFunction.displayName ?? transformationFunction.name
                               }}</span>
                <span v-if="slicingFunction"> on {{ slicingFunction.displayName ?? slicingFunction.name }}</span>
            </span>
            <div class="d-flex flex-row gap-4">
                <v-chip v-if="!compact" v-for="tag in sorted(suiteTest.test.tags)" x-small :color="pasterColor(tag)"
                        label>
                    {{ tag }}
                </v-chip>
            </div>
            <div class="flex-grow-1"/>
            <div v-if="result"
                 :class="`d-flex flex-row align-center gap-8 ${result.passed ? 'test-passed' : 'test-failed'}`">
                <span v-if="result.metric" class="metric"
                >Measured <b>Metric = {{
                        result.metric
                    }}</b></span>
                <v-chip v-if="result.passed" small :color="Colors.PASS_SURFACE" :text-color="Colors.ON_PASS_SURFACE"
                        label>
                    <v-icon>done</v-icon>
                    Passed
                </v-chip>
                <v-chip v-else small :color="Colors.FAIL_SURFACE" :text-color="Colors.ON_FAIL_SURFACE" label>
                    <v-icon>block</v-icon>
                    Failed
                </v-chip>
                <v-btn color="primary" outlined small>
                    <v-icon>info</v-icon>
                    Debug
                </v-btn>
            </div>
        </div>
        <div class="d-flex flex-row align-end test-card-footer">
            <div v-for="({name, value}) in orderedParams" class="d-flex flex-column">
                <span>{{ name }}</span>
                <span class="text-black">{{ value }}</span>
            </div>
            <div class="flex-grow-1"/>
            <v-btn text x-small @click="editTests">
                <v-icon>settings</v-icon>
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
import {pasterColor} from "@/utils";
import _ from "lodash";
import {Colors} from "@/utils/colors";
import {$vfm} from "vue-final-modal";
import SuiteTestInfoModal from "@/views/main/project/modals/SuiteTestInfoModal.vue";
import {useTestSuiteStore} from "@/stores/test-suite";

const {slicingFunctionsByUuid, transformationFunctionsByUuid} = storeToRefs(useCatalogStore())
const {models, datasets} = storeToRefs(useTestSuiteStore())

const props = defineProps<{
    suiteTest: SuiteTestDTO,
    result?: SuiteTestExecutionDTO,
    compact: boolean
}>();

const params = computed(() => props.result?.inputs);

function mapValue(value: string, type: string): string {
    if (type === 'SlicingFunction') {
        let slicingFunction = slicingFunctionsByUuid.value[value];
        return slicingFunction.displayName ?? slicingFunction.name
    } else if (type === 'TransformationFunction') {
        let transformationFunction = transformationFunctionsByUuid.value[value];
        return transformationFunction.displayName ?? transformationFunction.name
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
        .filter(({name}) => params.value!.hasOwnProperty(name))
        .map(({name, type}) => ({
            name: name.split('_').map(word => word[0].toUpperCase() + word.slice(1)).join(' '),
            value: mapValue(params.value[name], type)
        }))
    : [])

const slicingFunction = computed(() => {
    const uuid = params.value ? params.value['slicing_function'] : undefined;

    if (uuid) {
        return slicingFunctionsByUuid[uuid];
    } else {
        return undefined;
    }
})

const transformationFunction = computed(() => {
    const uuid = params.value ? params.value['transformation_function'] : undefined;

    if (uuid) {
        return transformationFunctionsByUuid[uuid];
    } else {
        return undefined;
    }
})

function sorted(arr: any[]) {
    const res = _.cloneDeep(arr);
    res.sort()
    return res;
}


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
    padding: 8px;
    gap: 16px;
}

.test-card-footer {
    border-top: 1px solid #dee2e6;
    padding: 8px;
    gap: 16px;
}


.test-name {
    max-width: 250px;
}

.gap-4 {
    gap: 8px;
}

.gap-8 {
    gap: 8px;
}

.test-failed {
    .metric {
        color: #dc3545;
    }
}

.text-black {
    color: black;
}
</style>

