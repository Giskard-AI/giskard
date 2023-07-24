<template>
    <v-dialog>
        <template v-slot:activator="{ on, attrs }">
            <v-btn text small v-on="on"> View More </v-btn>
        </template>
        <template v-slot:default="dialog">
            <v-card elevation="10">
                <v-card-title class="h1">
                    <span>Results</span>
                </v-card-title>
                <v-card-text>
                    <v-row class="text-center">
                        <v-col cols="6" class="pt-0">
                            <div> Prediction </div>

                            <v-tooltip bottom>
                                <template v-slot:activator="{ on, attrs }">
                                    <div v-on="prediction.length > maxLengthDisplayedCategoryCard ? on : ''" :class="classColorPrediction" class="text-h6"> {{ abbreviateMiddle(prediction, maxLengthDisplayedCategoryCard) }}</div>
                                </template>
                                <span>{{ prediction }}</span>
                            </v-tooltip>

                        </v-col>
                        <v-col cols="6" class="pt-0 pb-5">
                            <div> Actual </div>

                            <v-tooltip bottom>
                                <template v-slot:activator="{ on, attrs }">
                                    <div class="text-h6">
                                        <div v-if="isDefined(actual)">
                                            <div v-on="actual.length > maxLengthDisplayedCategoryCard ? on : ''"> {{ abbreviateMiddle(actual, maxLengthDisplayedCategoryCard) }}</div>
                                        </div>
                                        <div v-else> - </div>
                                    </div>
                                </template>
                                <span class="predict"> {{ actual }}</span>
                            </v-tooltip>

                        </v-col>
                    </v-row>
                    <v-row align="center">
                        <v-col cols="4">
                            <v-text-field dense solo hide-details clearable class="mx-2 mb-2 flex-1" v-model="search" append-icon="mdi-magnify" label="Search"></v-text-field>
                        </v-col>
                        <span>
                            ({{ numberDisplayed }} of {{ totalCategories }})
                        </span>
                    </v-row>
                    <v-chart class="chart pr-5" :option="chartOptions" :init-options="chartInit" autoresize />
                </v-card-text>
                <v-card-actions class="justify-end">
                    <v-btn text @click="dialog.value = false">Close</v-btn>
                </v-card-actions>
            </v-card>
        </template>
    </v-dialog>
</template>

<script setup lang="ts">
import * as _ from "lodash";
import { ref, onMounted, computed } from "vue";
import { use } from "echarts/core";
import { SVGRenderer } from "echarts/renderers";
import { BarChart } from "echarts/charts";
import { DataZoomSliderComponent, DataZoomInsideComponent, GridComponent } from "echarts/components"
import { abbreviateMiddle, maxLengthDisplayedCategory } from "@/results-utils";

use([SVGRenderer, BarChart, GridComponent, DataZoomSliderComponent, DataZoomInsideComponent]);


interface Props {
    resultProbabilities: { [key: string]: number };
    prediction: string;
    actual: string;
    classColorPrediction: string;
}

const props = defineProps<Props>();

const chartInit = {
    renderer: 'svg'
}

const search = ref("");
const showSlider = ref(true);
const numberDisplayed = ref(0);
const sizeResultCard = ref(0);

onMounted(() => {
    sizeResultCard.value = 9 * window.innerWidth / 10;
    window.addEventListener('resize', () => {
        sizeResultCard.value = 9 * window.innerWidth / 10;
    })
});

const totalCategories = computed(() => Object.keys(props.resultProbabilities).length);

const maxLengthDisplayedCategoryCard = computed(() => maxLengthDisplayedCategory(sizeResultCard.value));

function isDefined(val: any) {
    return !_.isNil(val);
}

const chartOptions = computed(() => {
    let maxPercentage = Math.max(...Object.values(props.resultProbabilities));
    const maxShown = maxPercentage + (20 * maxPercentage) / 100;
    showSlider.value = Object.keys(props.resultProbabilities).length > 20;
    let max = maxLengthDisplayedCategoryCard.value;
    let s = search.value;
    let results = Object.fromEntries(
        Object.entries(props.resultProbabilities)
            .filter(function (element) {
                let key = element[0];
                if (isDefined(s))
                    return key.toLocaleLowerCase().includes(s.toLocaleLowerCase());
                else
                    return true;
            }
            )
            .sort((a, b) => b[0].localeCompare(a[0]))
            .map(function (elt) {
                elt[0] = abbreviateMiddle(elt[0], max);
                return elt;
            })
    );
    numberDisplayed.value = Object.keys(results).length;
    return {
        xAxis: {
            type: "value",
            min: 0,
            max: maxShown,
        },
        yAxis: {
            type: "category",
            data: Object.keys(results),
            axisLabel: {
                interval: 0,
            },
        },
        series: [
            {
                type: "bar",
                label: {
                    show: true,
                    position: "right",
                    formatter: (params) =>
                        params.value % 1 == 0
                            ? params.value
                            : params.value.toFixed(3).toLocaleString(),
                },
                data: Object.values(results),
            },
        ],
        grid: {
            width: "80%",
            height: "80%",
            top: "10%",
            left: "10%",
            right: "10%",
            containLabel: true,
        },
        color: ["#0091EA"],
        dataZoom: [
            {
                type: 'inside',
                yAxisIndex: 0,
                minValueSpan: 15,
                maxValueSpan: 15,
                zoomOnMouseWheel: false,
                moveOnMouseWheel: true,
                moveOnMouseMove: false,
                start: 100,
            },
            {
                show: showSlider.value,
                showDetail: false,
                maxValueSpan: 15,
                brushSelect: false,
                yAxisIndex: 0,
                right: 10,
                width: 15,
                start: 100,
            },
        ]
    };
})

</script>

<style scoped>
.chart {
    height: 420px;
}

.v-tooltip__content {
    max-width: 500px !important;
    overflow-wrap: anywhere;
}
</style>