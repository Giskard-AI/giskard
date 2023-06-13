import {PushDTO} from "@/generated-sources";
import {defineStore} from "pinia";
import {api} from "@/api";

interface State {
    pushes: { [modelId: string]: { [datasetId: string]: { [rowNb: number]: PushDTO[] } } };
}

export const usePushStore = defineStore('push', {
    state: (): State => ({
        pushes: {}
    }),
    getters: {},
    actions: {
        async fetchPushSuggestions(modelId: string, datasetId: string, rowNb: number) {
            if (!this.pushes[modelId]) {
                this.pushes[modelId] = {};
            }
            if (!this.pushes[modelId][datasetId]) {
                this.pushes[modelId][datasetId] = {};
            }

            if (this.pushes[modelId][datasetId][rowNb]) {
                return this.pushes[modelId][datasetId][rowNb];
            }

            this.pushes[modelId][datasetId][rowNb] = await api.getPushes(modelId, datasetId, rowNb);
            return this.pushes[modelId][datasetId][rowNb];
        },
        getPushSuggestions(modelId: string, datasetId: string, rowNb: number) {
            if (!this.pushes[modelId]) {
                this.pushes[modelId] = {};
            }
            if (!this.pushes[modelId][datasetId]) {
                this.pushes[modelId][datasetId] = {};
            }

            return this.pushes[modelId][datasetId][rowNb];
        }
    }
})