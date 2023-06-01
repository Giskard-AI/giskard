import {ParameterizedCallableDTO} from "@/generated-sources";
import {defineStore} from "pinia";


interface State {
    transformationFunctions: { [column: string]: ParameterizedCallableDTO },
}


export const useInspectionStore = defineStore('inspection', {
    state: (): State => ({
        transformationFunctions: {}
    })
});
