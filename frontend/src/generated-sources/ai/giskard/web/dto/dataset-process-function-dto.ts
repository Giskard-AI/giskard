import type {CallableDTO} from './callable-dto';
import type {DatasetProcessFunctionType} from './dataset-process-function-type';

/**
 * Generated from ai.giskard.web.dto.DatasetProcessFunctionDTO
 */
export interface DatasetProcessFunctionDTO extends CallableDTO {
    cellLevel: boolean;
    clauses: {[key: string]: any}[];
    columnType?: string | null;
    processType: DatasetProcessFunctionType;
    projectKey: string;
}