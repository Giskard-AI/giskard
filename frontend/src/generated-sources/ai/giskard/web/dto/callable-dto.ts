import type {TestFunctionArgumentDTO} from './test-function-argument-dto';

/**
 * Generated from ai.giskard.web.dto.CallableDTO
 */
export interface CallableDTO {
    args: TestFunctionArgumentDTO[];
    code: string;
    displayName: string;
    doc: string;
    module: string;
    moduleDoc: string;
    name: string;
    potentiallyUnavailable: boolean;
    tags: string[];
    uuid: any /* TODO: Missing translation of java.util.UUID */;
    version?: number | null;
}