<template>
    <v-dialog>
        <template v-slot:activator="{ on, attrs }">
            <v-btn text small v-on="on"> View More </v-btn>
        </template>
        <template v-slot:default="dialog">
            <v-card class="p-2" elevation="10">
                <v-card-title class="h1">
                    <span>Results</span>
                    <v-spacer/>
                    <v-text-field
                        dense
                        solo
                        hide-details
                        clearable
                        class="mx-2 flex-1"
                        v-model="search"
                        append-icon="mdi-magnify"
                        label="Search"
                    ></v-text-field>
                </v-card-title>
                <v-card-text elevation>
                    <v-chart class="chart" :option="chartOptions" autoresize/>
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
import {Component, Prop, Vue, Watch} from 'vue-property-decorator';
import {use} from "echarts/core";
import ECharts from "vue-echarts";
import {CanvasRenderer} from "echarts/renderers";
import {BarChart} from "echarts/charts";
import {GridComponent} from "echarts/components";
import {DataZoomSliderComponent} from "echarts/components"
import {DataZoomInsideComponent} from "echarts/components"

use([CanvasRenderer, BarChart, GridComponent, DataZoomSliderComponent, DataZoomInsideComponent]);
Vue.component("v-chart", ECharts);

@Component
export default class ResultPopover extends Vue {
    @Prop({required: true}) resultProbabilities!: {[key: string]: number};

    search: string = "";
    showSlider : boolean = true;

    get chartOptions() {
        let maxPercentage = Math.max(...Object.values(this.resultProbabilities));
        const maxShown = maxPercentage + (20 * maxPercentage) / 100;
        this.showSlider = Object.keys(this.resultProbabilities).length > 20
        let s = this.search;
        let results = Object.fromEntries(
            Object.entries(this.resultProbabilities)
                .filter(function (element)
                    { 
                        let key = element[0];
                        return key.toLocaleLowerCase().includes(s.toLocaleLowerCase())
                    }
                )
                .sort((a, b) => b[0].localeCompare(a[0]))
        );
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
            tooltip: {
                trigger: 'item'
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
        height: 450px;

    }
</style>