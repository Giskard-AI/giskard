import type {FunctionInputDTO} from './function-input-dto';
import type {TestFunctionDTO} from './test-function-dto';

/**
 * Generated from ai.giskard.web.dto.SuiteTestDTO
 */
export interface SuiteTestDTO {
    functionInputs: {[key: string]: FunctionInputDTO};
    id?: number | null;
    test: TestFunctionDTO;
    testUuid: any /* TODO: Missing translation of java.util.UUID */;
}