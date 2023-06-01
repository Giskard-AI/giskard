import type {FunctionInputDTO} from './function-input-dto';
import type {SuiteTestDTO} from './suite-test-dto';

/**
 * Generated from ai.giskard.web.dto.TestSuiteDTO
 */
export interface TestSuiteDTO {
    functionInputs: FunctionInputDTO[];
    id?: number | null;
    name: string;
    projectKey?: string | null;
    tests: SuiteTestDTO[];
}