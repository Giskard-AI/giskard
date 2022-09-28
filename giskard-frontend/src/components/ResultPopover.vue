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
                            <div > Prediction </div>

                            <v-tooltip bottom>
                                <template v-slot:activator="{ on, attrs }">
                                    <div v-on="prediction.length > maxCharsCategory ? on : ''" :class="classColorPrediction" class="text-h6">  {{ abbreviateMiddle(prediction, maxCharsCategory / 2, maxCharsCategory) }}</div>
                                </template>
                                <span>{{prediction}}</span>
                            </v-tooltip>

                        </v-col>
                        <v-col cols="6" class="pt-0 pb-5">
                            <div > Actual </div>

                            <v-tooltip bottom>
                                <template v-slot:activator="{ on, attrs }">
                                    <div class="text-h6">
                                        <div v-if="isDefined(actual)">
                                            <div v-on="actual.length > maxCharsCategory ? on : ''"> {{ abbreviateMiddle(actual, maxCharsCategory / 2,  maxCharsCategory) }}</div>
                                        </div> 
                                        <div v-else> - </div>
                                    </div>
                                </template>
                                <span class="predict"> {{actual}}</span>
                            </v-tooltip>

                        </v-col>
                    </v-row>
                    <v-row align="center">
                        <v-col cols="4">
                            <v-text-field
                                dense
                                solo
                                hide-details
                                clearable
                                class="mx-2 mb-2 flex-1"
                                v-model="search"
                                append-icon="mdi-magnify"
                                label="Search"
                            ></v-text-field>
                        </v-col>
                        <span>
                            ({{ numberDisplayed }} of {{ totalCategories }})
                        </span>
                    </v-row>
                    <v-chart class="chart pr-5" :option="chartOptions" :init-options="chartInit" autoresize/>
                </v-card-text>
                <v-card-actions class="justify-end">
                    <v-btn
                    text
                    @click="dialog.value = false"
                    >Close</v-btn>
                </v-card-actions>
            </v-card>
        </template>
    </v-dialog>
</template>

<script lang="ts">
import * as _ from "lodash";
import {Component, Prop, Vue} from 'vue-property-decorator';
import {use} from "echarts/core";
import ECharts from "vue-echarts";
import {SVGRenderer} from "echarts/renderers";
import {BarChart} from "echarts/charts";
import {GridComponent} from "echarts/components";
import {DataZoomSliderComponent} from "echarts/components"
import {DataZoomInsideComponent} from "echarts/components"
import {abbreviateMiddle} from "@/utils";

use([SVGRenderer, BarChart, GridComponent, DataZoomSliderComponent, DataZoomInsideComponent]);
Vue.component("v-chart", ECharts);

@Component
export default class ResultPopover extends Vue {
    @Prop({required: true}) resultProbabilities!: {[key: string]: number};
    @Prop({required: true}) prediction!: string;
    @Prop({required: true}) actual!: string;
    @Prop({required: true}) classColorPrediction!: string;

    search: string = "";
    showSlider : boolean = true;
    numberDisplayed : number = 0;
    windowWidth = window.innerWidth;

    abbreviateMiddle = abbreviateMiddle;
    
    async mounted() {  
        window.addEventListener('resize', () => {
        this.windowWidth = window.innerWidth
        })
    }

    get totalCategories(){
        return Object.keys(this.resultProbabilities).length;
    }

    get maxCharsCategory(){
        switch (this.$vuetify.breakpoint.name) {
            case 'xs': return 10
            case 'sm': return 20
            case 'md': return 30
            case 'lg': return 50
            case 'xl': return 70
        }
    }

    isDefined(val: any) {
        return !_.isNil(val);
    }

    get chartInit(){
        return {
            renderer: 'svg'
        }
    }

    get chartOptions() {
        let maxPercentage = Math.max(...Object.values(this.resultProbabilities));
        const maxShown = maxPercentage + (20 * maxPercentage) / 100;
        this.showSlider = Object.keys(this.resultProbabilities).length > 20;
        let max = this.maxCharsCategory;
        let s = this.search;
        let def = this.isDefined;
        let results = Object.fromEntries(
            Object.entries(this.resultProbabilities)
                .filter(function (element)
                    { 
                        let key = element[0];
                        if (def(s))
                            return key.toLocaleLowerCase().includes(s.toLocaleLowerCase());
                        else
                            return true;
                    }
                )
                .sort((a, b) => b[0].localeCompare(a[0]))
                .map(function (elt){
                    elt[0] = abbreviateMiddle(elt[0], max/2, max);
                    return elt;
                })
        );
        this.numberDisplayed = Object.keys(results).length;
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
                    start:100,
                },
                {
                    show: this.showSlider,
                    showDetail: false,
                    maxValueSpan: 15,
                    brushSelect: false,
                    yAxisIndex: 0,
                    right: 10,
                    width:15,
                    start:100,
                },
            ]
        };
  }


}

</script>

<style>
    .chart{
        height: 420px;
    }
    .v-tooltip__content {
        max-width: 500px !important;
        overflow-wrap: anywhere;
    }
</style>