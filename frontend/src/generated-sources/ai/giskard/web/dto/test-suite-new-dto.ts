import type {SuiteTestDTO} from './suite-test-dto';

/**
 * Generated from ai.giskard.web.dto.TestSuiteNewDTO
 */
export interface TestSuiteNewDTO {
    id?: number | null;
    name: string;
    projectKey?: string | null;
    tests: SuiteTestDTO[];
}