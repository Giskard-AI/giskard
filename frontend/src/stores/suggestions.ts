import {PushDTO} from "@/generated-sources";
import {defineStore} from "pinia";
import {api} from "@/api";

interface State {
    suggestions: { [modelId: string]: { [datasetId: string]: { [rowNb: number]: PushDTO[] } } };
}

export const usePushStore = defineStore('push', {
    state: (): State => ({
        suggestions: {}
    }),
    getters: {},
    actions: {
        async fetchPushSuggestions(modelId: string, datasetId: string, rowNb: number) {
            if (!this.suggestions[modelId]) {
                this.suggestions[modelId] = {};
            }
            if (!this.suggestions[modelId][datasetId]) {
                this.suggestions[modelId][datasetId] = {};
            }

            if (this.suggestions[modelId][datasetId][rowNb]) {
                return this.suggestions[modelId][datasetId][rowNb];
            }

            this.suggestions[modelId][datasetId][rowNb] = await api.getSuggestions(modelId, datasetId, rowNb);
            return this.suggestions[modelId][datasetId][rowNb];
        },
        getPushSuggestions(modelId: string, datasetId: string, rowNb: number) {
            if (!this.suggestions[modelId]) {
                this.suggestions[modelId] = {};
            }
            if (!this.suggestions[modelId][datasetId]) {
                this.suggestions[modelId][datasetId] = {};
            }

            return this.suggestions[modelId][datasetId][rowNb];
        }
    }
})