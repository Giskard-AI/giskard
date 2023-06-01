import type {SuiteTestDTO} from './suite-test-dto';
import type {TestInputDTO} from './test-input-dto';

/**
 * Generated from ai.giskard.web.dto.TestSuiteDTO
 */
export interface TestSuiteDTO {
    id?: number | null;
    name: string;
    projectKey?: string | null;
    testInputs: TestInputDTO[];
    tests: SuiteTestDTO[];
}