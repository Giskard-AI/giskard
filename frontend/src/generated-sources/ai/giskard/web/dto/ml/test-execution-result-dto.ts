import type {NamedSingleTestResultDTO} from './named-single-test-result-dto';
import type {TestResult} from './../../../domain/ml/test-result';

/**
 * Generated from ai.giskard.web.dto.ml.TestExecutionResultDTO
 */
export interface TestExecutionResultDTO {
    executionDate: any /* TODO: Missing translation of java.time.Instant */;
    message: string;
    result: NamedSingleTestResultDTO[];
    status: TestResult;
    testId: number;
    testName: string;
}