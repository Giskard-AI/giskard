import type {TestFunctionArgumentDTO} from './test-function-argument-dto';

/**
 * Generated from ai.giskard.web.dto.TestDefinitionDTO
 */
export interface TestDefinitionDTO {
    arguments: {[key: string]: TestFunctionArgumentDTO};
    code: string;
    doc: string;
    id: string;
    module: string;
    moduleDoc: string;
    name: string;
    tags: string[];
}