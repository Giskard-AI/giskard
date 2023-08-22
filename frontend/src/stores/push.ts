import {PushActionDTO, PushDTO} from "@/generated-sources";
import {defineStore} from "pinia";
import {api} from "@/api";

interface State {
    pushes: { [key: string]: Pushes };
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
        identifier: undefined,
    }),
    getters: {},
    actions: {
        async fetchPushSuggestions(modelId: string, datasetId: string, rowNb: number, inputData: any, modelFeatures: string[]) {
            this.identifier = {modelId, datasetId, rowNb, inputData, modelFeatures};
            let identifierString = JSON.stringify({modelId, datasetId, rowNb, inputData, modelFeatures});
            let previous = this.current;
            this.current = undefined;

            let result = await api.getPushes(modelId, datasetId, rowNb, inputData);

            if (previous == result) {
                return;
            }

            let currentIdentifier = JSON.stringify(this.identifier);
            if (currentIdentifier === identifierString) {
                console.log("Setting pushes")
                // @ts-ignore
                this.current = result;
            }

            return this.current;
        },
        async applyPush(pushKind: string, ctaKind: string): Promise<PushActionDTO> {
            let result = await api.applyPush(this.identifier!.modelId, this.identifier!.datasetId, this.identifier!.rowNb, pushKind, ctaKind, this.identifier!.inputData);
            // @ts-ignore
            return result;
        }
    }
})