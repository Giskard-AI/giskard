<template>
  <div class="fill-height overflow-auto">

    <code>Test suites new</code>
    <pre>{{ suites }}</pre>
    <pre style="color: lightcoral">{{ registry }}</pre>
  </div>
</template>

<script lang="ts" setup>

import {api} from "@/api";
import {onMounted, ref} from "vue";
import {TestSuiteNewDTO} from "@/generated-sources";

const props = defineProps<{
  projectId: number
}>();

let suites = ref<TestSuiteNewDTO[]>([]);
let registry = ref<Array<any>>([]);
onMounted(async () => {
  registry.value = await api.getTestsRegistry(props.projectId);
  suites.value = await api.getTestSuitesNew(props.projectId);
})


</script>