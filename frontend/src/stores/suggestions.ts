import {PushDTO} from "@/generated-sources";
import {defineStore} from "pinia";
import {api} from "@/api";

interface State {
    pushes: { [modelId: string]: { [datasetId: string]: { [rowNb: number]: Pushes } } };
    current: Pushes | undefined;
}

interface Pushes {
    perturbation: PushDTO,
    contribution: PushDTO,
    borderline: PushDTO,
    overconfidence: PushDTO
}

export const usePushStore = defineStore('push', {
    state: (): State => ({
        pushes: {},
        current: undefined
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
                this.current = this.pushes[modelId][datasetId][rowNb];
                return this.pushes[modelId][datasetId][rowNb];
            }

            // @ts-ignore
            this.pushes[modelId][datasetId][rowNb] = await api.getPushes(modelId, datasetId, rowNb);
            this.current = this.pushes[modelId][datasetId][rowNb];
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