import type {FunctionInputDTO} from './function-input-dto';
import type {GenerateTestSuiteInputDTO} from './generate-test-suite-input-dto';

/**
 * Generated from ai.giskard.web.dto.GenerateTestSuiteDTO
 */
export interface GenerateTestSuiteDTO {
    inputs: GenerateTestSuiteInputDTO[];
    name: string;
    sharedInputs: FunctionInputDTO[];
}