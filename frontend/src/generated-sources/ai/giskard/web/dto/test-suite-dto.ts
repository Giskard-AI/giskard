import type {SuiteTestDTO} from './suite-test-dto';

/**
 * Generated from ai.giskard.web.dto.TestSuiteDTO
 */
export interface TestSuiteDTO {
    id: number;
    name: string;
    projectKey: string;
    tests: SuiteTestDTO[];
}