import {defineStore} from 'pinia';

interface State {
    currentExecution: number | null,
    compareSelectedItems: Array<number> | null
}

export const useTestSuiteCompareStore = defineStore('testSuiteCompare', {
    state: (): State => ({
        currentExecution: null,
        compareSelectedItems: null
    }),
    getters: {},
    actions: {
        setCurrentExecution(id: number | null) {
            this.currentExecution = id;
        },
        reset() {
            this.currentExecution = null;
            this.compareSelectedItems = null;
        },
    }
});
