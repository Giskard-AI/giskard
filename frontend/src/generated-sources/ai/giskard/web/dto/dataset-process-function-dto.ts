import type {CallableDTO} from './callable-dto';

/**
 * Generated from ai.giskard.web.dto.DatasetProcessFunctionDTO
 */
export interface DatasetProcessFunctionDTO extends CallableDTO {
    cellLevel: boolean;
    columnType?: string | null;
    noCode: boolean;
}