import type {CodeLanguage} from './../../../domain/ml/code-language';
import type {TestResult} from './../../../domain/ml/test-result';
import type {TestType} from './../../../domain/ml/test-type';

/**
 * Generated from ai.giskard.service.dto.ml.TestDTO
 */
export interface TestDTO {
    code: string;
    id: number;
    language: CodeLanguage;
    lastExecutionDate: any /* TODO: Missing translation of java.util.Date */;
    name: string;
    status: TestResult;
    suiteId: number;
    type: TestType;
}