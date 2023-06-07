import {ParameterizedCallableDTO} from "@/generated-sources";
import {defineStore} from "pinia";


interface State {
    transformationFunctions: { [column: string]: ParameterizedCallableDTO },
}


export const useInspectionStore = defineStore('inspection', {
    state: (): State => ({
        transformationFunctions: {}
    }),
    actions: {
        setTransformation(column: string, callable: Partial<ParameterizedCallableDTO>) {
            if (callable.uuid) {
                this.transformationFunctions = {
                    ...this.transformationFunctions,
                    [column]: callable as ParameterizedCallableDTO
                }
            } else {
                delete this.transformationFunctions[column]
                this.transformationFunctions = {...this.transformationFunctions}

            }
        }
    }
});
