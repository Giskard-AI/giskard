<template>
    <v-menu offset-x :close-on-content-click="false" v-model="opened">

        <template v-slot:activator="{ on: onMenu }">

            <v-tooltip right>
                <template v-slot:activator="{ on: onTooltip }">
                    <v-btn small icon
                           :color="hasTransformation ? 'primary' : 'grey'"
                           v-on="{ ...onMenu, ...onTooltip }">
                        <v-icon size=18>mdi-swap-horizontal</v-icon>
                    </v-btn>
                </template>
                <span>Apply a transformation</span>
            </v-tooltip>
        </template>

        <v-card dark color="primary">
            <v-card-title>
                <p>Transformation for '{{ column }}'</p>
            </v-card-title>
            <v-card-text>
                <TransformationFunctionSelector label="Transformation to apply"
                                                :column-type="columnType"
                                                :column-name="column"
                                                :value.sync="transformation.uuid"
                                                :args.sync="transformation.params"
                                                @onChanged="handleOnChanged"/>
            </v-card-text>
            <v-card-actions>
            </v-card-actions>
        </v-card>
    </v-menu>
</template>

<script setup lang="ts">

import {storeToRefs} from "pinia";
import {useInspectionStore} from "@/stores/inspection";
import {computed, ref} from "vue";
import TransformationFunctionSelector from "@/views/main/utils/TransformationFunctionSelector.vue";
import {ParameterizedCallableDTO} from "@/generated-sources";

const props = defineProps<{
    projectId: number
    column: string,
    columnType: string
}>()

const transformation = ref<Partial<ParameterizedCallableDTO>>({
    uuid: undefined,
    params: [],
    type: 'TRANSFORMATION'
})
const opened = ref<boolean>(false);

let inspectionStore = useInspectionStore();
const {transformationFunctions} = storeToRefs(inspectionStore)

const hasTransformation = computed(() => transformationFunctions.hasOwnProperty(props.column));

function handleOnChanged() {
    inspectionStore.setTransformation(props.column, transformation.value);
}

</script>

<style scoped lang="scss">
div.v-card {

    opacity: 0.98;
    max-width: 500px;

    & > *:nth-child(-n + 2) { // for the first two children: the title and the content
        padding-bottom: 0px;
    }

    .v-card__title {
        font-size: 1rem;
        padding-top: 8px;
        word-break: normal;
        line-height: 22px;
    }

    .v-input {
        margin-top: 4px;
        margin-bottom: 6px;
    }

    .v-card__actions {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        font-size: 13px;
        color: white;

        * {
            margin: 0 3px
        }
    }
}

.v-chip {
    padding: 8px
}
</style>
