import type {TestFunctionDTO} from './test-function-dto';
import type {TestInputDTO} from './test-input-dto';

/**
 * Generated from ai.giskard.web.dto.SuiteTestDTO
 */
export interface SuiteTestDTO {
    id?: number | null;
    test: TestFunctionDTO;
    testInputs: {[key: string]: TestInputDTO};
    testUuid: string;
}