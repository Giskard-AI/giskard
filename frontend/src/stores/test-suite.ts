import {ProjectDTO, TestSuiteNewDTO} from '@/generated-sources';
import {defineStore} from 'pinia';

interface TestSuiteState {
    testSuites: TestSuiteNewDTO[],
    testSuite: TestSuiteNewDTO | null
}

export const useTestSuiteStore = defineStore('testSuite', {
    state: (): TestSuiteState => ({
        testSuites: [],
        testSuite: null
    }),
    getters: {},
    actions: {

    }
});
