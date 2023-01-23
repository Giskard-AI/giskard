import type {SuiteTestExecutionDTO} from './suite-test-execution-dto';
import type {TestResult} from './../../../domain/ml/test-result';
import type {WorkerJobDTO} from './worker-job-dto';

/**
 * Generated from ai.giskard.web.dto.ml.TestSuiteExecutionDTO
 */
export interface TestSuiteExecutionDTO extends WorkerJobDTO {
    id: number;
    inputs: {[key: string]: string};
    result?: TestResult | null;
    results?: SuiteTestExecutionDTO[] | null;
    suiteId: number;
}