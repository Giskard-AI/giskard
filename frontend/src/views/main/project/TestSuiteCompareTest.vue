<template>
  <div>
    <p class="text-h4">{{ registry.tests[route.params.testId].name }}</p>
    <v-chart
        v-if="props.executions"
        class="chart"
        :option="graphOptions"
        autoresize
    />
  </div>
</template>

<script lang="ts" setup>

import {SuiteTestExecutionDTO, TestCatalogDTO, TestSuiteExecutionDTO} from '@/generated-sources';
import {computed} from 'vue';
import {useRoute} from 'vue-router/composables';
import {use} from 'echarts/core';
import {LineChart} from 'echarts/charts';
import {EChartsOption} from 'echarts';
import {Colors} from '@/utils/colors';
import moment from 'moment';

use([LineChart]);

const props = defineProps<{
  executions?: TestSuiteExecutionDTO[],
  registry: TestCatalogDTO,
}>();

const route = useRoute();

type ComparedTestExecution = {
  execution: TestSuiteExecutionDTO,
  test: SuiteTestExecutionDTO
};

const graphOptions = computed(() => {
  if (!props.executions) {
    return null;
  }

  const results: ComparedTestExecution[] = [...props.executions]
      .reverse()
      .map(execution => ({
        execution,
        test: execution.results?.find(result => result.test.testId === route.params.testId)
      }))
      .filter(execution => execution.test !== undefined) as ComparedTestExecution[];

  return {
    legend: {},
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

