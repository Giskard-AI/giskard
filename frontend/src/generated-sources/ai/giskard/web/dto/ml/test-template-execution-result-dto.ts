import type {NamedSingleTestResultDTO} from './named-single-test-result-dto';
import type {TestResult} from './../../../domain/ml/test-result';

/**
 * Generated from ai.giskard.web.dto.ml.TestTemplateExecutionResultDTO
 */
export interface TestTemplateExecutionResultDTO {
    executionDate: any /* TODO: Missing translation of java.time.Instant */;
    message: string;
    result: NamedSingleTestResultDTO[];
    status: TestResult;
    testUuid: any /* TODO: Missing translation of java.util.UUID */;
}