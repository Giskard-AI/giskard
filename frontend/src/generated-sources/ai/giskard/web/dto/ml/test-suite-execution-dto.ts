import type {FunctionInputDTO} from './../function-input-dto';
import type {SuiteTestExecutionDTO} from './suite-test-execution-dto';
import type {TestResult} from './../../../domain/ml/test-result';

/**
 * Generated from ai.giskard.web.dto.ml.TestSuiteExecutionDTO
 */
export interface TestSuiteExecutionDTO {
    completionDate: any /* TODO: Missing translation of java.util.Date */;
    executionDate: any /* TODO: Missing translation of java.util.Date */;
    id: number;
    inputs: FunctionInputDTO[];
    logs?: string | null;
    message?: string | null;
    result?: TestResult | null;
    results?: SuiteTestExecutionDTO[] | null;
    suiteId: number;
}