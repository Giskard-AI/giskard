import type {SuiteTestDTO} from './suite-test-dto';

/**
 * Generated from ai.giskard.web.dto.TestSuiteNewDTO
 */
export interface TestSuiteNewDTO {
    id: number;
    name: string;
    projectKey: string;
    tests: SuiteTestDTO[];
}