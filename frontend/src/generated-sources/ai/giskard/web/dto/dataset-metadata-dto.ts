import type {ColumnType} from '../../domain/column-type';

/**
 * Generated from ai.giskard.web.dto.DatasetMetadataDTO
 */
export interface DatasetMetadataDTO {
    columnDTypes?: {[key: string]: string} | null;
    columnTypes: {[key: string]: ColumnType};
    id: string;
    name: string;
    target?: string | null;
}