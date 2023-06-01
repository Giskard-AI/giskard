import type {CallableDTO} from './callable-dto';
import type {DatasetProcessFunctionType} from './dataset-process-function-type';

/**
 * Generated from ai.giskard.web.dto.DatasetProcessFunctionDTO
 */
export interface DatasetProcessFunctionDTO extends CallableDTO {
    cellLevel: boolean;
    columnType?: string | null;
    processType: DatasetProcessFunctionType;
}