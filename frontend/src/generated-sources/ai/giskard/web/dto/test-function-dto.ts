import type {CallableDTO} from './callable-dto';

/**
 * Generated from ai.giskard.web.dto.TestFunctionDTO
 */
export interface TestFunctionDTO {
    args: TestFunctionArgumentDTO[];
    code: string;
    displayName: string;
    doc: string;
    module: string;
    moduleDoc: string;
    name: string;
    tags: string[];
    uuid: any /* TODO: Missing translation of java.util.UUID */;
    version: number;
}
