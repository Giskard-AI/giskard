import type {ColumnType} from './../../domain/column-type';

/**
 * Generated from ai.giskard.web.dto.DatasetMetadataDTO
 */
export interface DatasetMetadataDTO {
    columnDtypes?: {[key: string]: string} | null;
    columnTypes: {[key: string]: ColumnType};
    id: string;
    name: string;
    target?: string | null;
}