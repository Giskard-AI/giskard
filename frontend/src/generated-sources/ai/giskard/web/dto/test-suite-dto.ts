import type {SuiteTestDTO} from './suite-test-dto';

/**
 * Generated from ai.giskard.web.dto.TestSuiteDTO
 */
export interface TestSuiteDTO {
    id?: number | null;
    name: string;
    projectKey?: string | null;
    tests: SuiteTestDTO[];
}
