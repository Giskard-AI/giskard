import type {FunctionInputDTO} from './function-input-dto';

/**
 * Generated from ai.giskard.web.dto.RunAdhocTestRequest
 */
export interface RunAdhocTestRequest {
    debug: boolean;
    inputs: FunctionInputDTO[];
    projectId: number;
    testUuid: string;
}