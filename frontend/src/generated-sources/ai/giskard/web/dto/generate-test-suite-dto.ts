import type {GenerateTestSuiteInputDTO} from './generate-test-suite-input-dto';
import type {TestInputDTO} from './test-input-dto';

/**
 * Generated from ai.giskard.web.dto.GenerateTestSuiteDTO
 */
export interface GenerateTestSuiteDTO {
    inputs: GenerateTestSuiteInputDTO[];
    name: string;
    sharedInputs: TestInputDTO[];
}