import {FunctionInputDTO, SuiteTestDTO} from "@/generated/client";

export class SuiteTestUtils {

    private SuiteTestUtils() {
        throw Error('Utils class')
    }

    private static computeDisplayName(displayName: string, functionInputs?: { [key: string]: FunctionInputDTO; }): string {
        return displayName.split(/({[a-zA-Z_]+})/gm)
            .map(part => {
                if (part.length <= 2 || !part.startsWith('{') || !part.endsWith('}')) {
                    return part;
                }

                const variable = part.substring(1, part.length - 1);
                if (functionInputs !== undefined && functionInputs.hasOwnProperty(variable) && !functionInputs[variable].isAlias) {
                    return functionInputs[variable].value;
                }

                return `{${variable} not found}`
            })
            .join('');
    }

    static getDisplayName(suiteTest: SuiteTestDTO): string {
        if (suiteTest.displayName !== undefined) {
            return SuiteTestUtils.computeDisplayName(suiteTest.displayName, suiteTest.functionInputs);
        }

        return suiteTest.test?.displayName ?? suiteTest.test?.name!;
    }

}
