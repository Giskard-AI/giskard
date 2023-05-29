import {defineStore} from 'pinia';

interface State {
    currentExecution: number | null,
    compareSelectedItems: Array<number>
}

export const useTestSuiteCompareStore = defineStore('testSuiteCompare', {
    state: (): State => ({
        currentExecution: null,
        compareSelectedItems: []
    }),
    getters: {},
    actions: {
        setCurrentExecution(id: number | null) {
            this.currentExecution = id;
        },
        reset() {
            this.currentExecution = null;
            this.compareSelectedItems = [];
        }
    }
});
