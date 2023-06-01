import type {CallableDTO} from './callable-dto';
import type {TestFunctionArgumentDTO} from './test-function-argument-dto';

/**
 * Generated from ai.giskard.web.dto.TestFunctionDTO
 */
export interface TestFunctionDTO extends CallableDTO {
    args: TestFunctionArgumentDTO[];
}