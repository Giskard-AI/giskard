import type {TestExecutionDto} from './test-execution-dto';
import type {TestResult} from './../../../domain/ml/test-result';

/**
 * Generated from ai.giskard.web.dto.ml.TestSuiteExecutionDTO
 */
export interface TestSuiteExecutionDTO {
    executionDate: any /* TODO: Missing translation of java.util.Date */;
    inputs: {[key: string]: string};
    result: TestResult;
    results: TestExecutionDto[];
    suiteId: number;
}