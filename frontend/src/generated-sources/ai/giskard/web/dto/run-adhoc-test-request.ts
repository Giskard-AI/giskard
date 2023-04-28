import type {FunctionInputDTO} from './function-input-dto';

/**
 * Generated from ai.giskard.web.dto.RunAdhocTestRequest
 */
export interface RunAdhocTestRequest {
    inputs: FunctionInputDTO[];
    projectId: number;
    testUuid: string;
}