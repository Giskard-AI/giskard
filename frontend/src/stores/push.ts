import {PushActionDTO, PushDTO} from "@/generated-sources";
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
    rowNb: number,
    inputData: any,
    modelFeatures: string[]
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
            this.identifier = {modelId, datasetId, rowNb, inputData, modelFeatures};
            this.current = undefined;

            // @ts-ignore
            this.current = await api.getPushes(modelId, datasetId, rowNb, inputData);
            return this.current;
        },
        async applyPush(pushKind: string, ctaKind: string): Promise<PushActionDTO> {
            let result = await api.applyPush(this.identifier!.modelId, this.identifier!.datasetId, this.identifier!.rowNb, pushKind, ctaKind, this.identifier!.inputData);
            // @ts-ignore
            return result;
        }
    }
})