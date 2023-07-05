import {PushDTO} from "@/generated-sources";
import {defineStore} from "pinia";
import {api} from "@/api";

interface State {
    pushes: { [modelId: string]: { [datasetId: string]: { [rowNb: number]: Pushes } } };
    current: Pushes | undefined;
    identifier: PushIdentifier | undefined;
}

interface Pushes {
    perturbation: PushDTO,
    contribution: PushDTO,
    borderline: PushDTO,
    overconfidence: PushDTO
}

interface PushIdentifier {
    modelId: string,
    datasetId: string,
    rowNb: number
}

export const usePushStore = defineStore('push', {
    state: (): State => ({
        pushes: {},
        current: undefined,
        identifier: undefined
    }),
    getters: {},
    actions: {
        async fetchPushSuggestions(modelId: string, datasetId: string, rowNb: number, inputData: any, modelFeatures: string[]) {
            this.identifier = {modelId, datasetId, rowNb};
            this.current = undefined;

            if (!this.pushes[modelId]) {
                this.pushes[modelId] = {};
            }
            if (!this.pushes[modelId][datasetId]) {
                this.pushes[modelId][datasetId] = {};
            }

            if (!this.pushes[modelId][datasetId][rowNb]) {
                // @ts-ignore
                this.pushes[modelId][datasetId][rowNb] = await api.getPushes(modelId, datasetId, rowNb, inputData, []);
            }

            this.current = this.pushes[modelId][datasetId][rowNb];
            return this.pushes[modelId][datasetId][rowNb];
        },
        async applyPush(pushKind: string, ctaKind: string) {
            let result = await api.applyPush(this.identifier!.modelId, this.identifier!.datasetId, this.identifier!.rowNb, pushKind, ctaKind);
            console.log(result);
        }
    }
})