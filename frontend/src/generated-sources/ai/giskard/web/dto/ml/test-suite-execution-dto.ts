import type {SingleTestResultDTO} from './single-test-result-dto';
import type {TestResult} from './../../../domain/ml/test-result';

/**
 * Generated from ai.giskard.web.dto.ml.TestSuiteExecutionDTO
 */
export interface TestSuiteExecutionDTO {
    executionDate: any /* TODO: Missing translation of java.util.Date */;
    inputs: {[key: string]: string};
    result: TestResult;
    results: {[key: string]: SingleTestResultDTO};
    suiteId: number;
}