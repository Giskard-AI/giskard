<template>
  <div v-if="registry">
    <p class="text-h4">{{ registry.tests[route.params.testId].name }}</p>
    <div style="height: 400px">
      <v-chart
          v-if="executions"
          class="chart"
          :option="graphOptions"
          autoresize
      />
    </div>

  </div>
  <v-progress-circular
      v-else
      size="100"
      indeterminate
      color="primary"
  ></v-progress-circular>
</template>

<script lang="ts" setup>

import {SuiteTestExecutionDTO, TestSuiteExecutionDTO} from '@/generated-sources';
import {computed} from 'vue';
import {useRoute} from 'vue-router/composables';
import {use} from 'echarts/core';
import {LineChart} from 'echarts/charts';
import {EChartsOption} from 'echarts';
import {Colors} from '@/utils/colors';
import moment from 'moment';
import {storeToRefs} from 'pinia';
import {useTestSuiteStore} from '@/stores/test-suite';
import {Vue} from 'vue-property-decorator';
import {CanvasRenderer} from 'echarts/renderers';
import {GridComponent} from 'echarts/components';
import ECharts from 'vue-echarts';

use([CanvasRenderer, LineChart, GridComponent]);
Vue.component("v-chart", ECharts);

const {executions, registry} = storeToRefs(useTestSuiteStore());

const route = useRoute();

type ComparedTestExecution = {
  execution: TestSuiteExecutionDTO,
  test: SuiteTestExecutionDTO
};

const graphOptions = computed(() => {
  if (!executions.value) {
    return null;
  }

  const results: ComparedTestExecution[] = [...executions.value]
      .reverse()
      .map(execution => ({
        execution,
        test: execution.results?.find(result => result.test.testId === route.params.testId)
      }))
      .filter(execution => execution.test !== undefined) as ComparedTestExecution[];

  return {
    xAxis: {
      data: results.map(result => moment(result.execution.executionDate).format('DD/MM/YYYY HH:mm'))
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        data: results.map(result => result.test?.metric),
        name: 'Metric',
        type: 'line',
        symbolSize: 10,
        lineStyle: {
          color: 'gray'
        },
        itemStyle: {
          color: (params) => results[params.dataIndex].test.passed ? Colors.PASS : Colors.FAIL
        }
      },
      {
        data: results.map(result => getThreshold(result.execution.inputs, result.test.inputs)),
        name: 'Threshold',
        type: 'line',
        step: 'middle',
        lineStyle: {
          color: 'gray',
          type: 'dashed'
        },
        itemStyle: {
          color: 'gray'
        },
      },
    ]
  } as EChartsOption
});

function getThreshold(globalInput: { [key: string]: string }, fixedInput: { [key: string]: string }): number | string {
  if (Object.hasOwn(fixedInput, 'threshold')) {
    return Number(fixedInput['threshold']);
  } else if (Object.hasOwn(globalInput, 'threshold')) {
    return Number(globalInput['threshold']);
  } else {
    // Missing data
    return '-';
  }
}

</script>

