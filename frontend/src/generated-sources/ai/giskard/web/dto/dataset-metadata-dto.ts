import type {ColumnType} from './../../domain/column-type';

/**
 * Generated from ai.giskard.web.dto.DatasetMetadataDTO
 */
export interface DatasetMetadataDTO {
    categoryFeatures: {[key: string]: string[]};
    columnDtypes?: {[key: string]: string} | null;
    columnTypes: {[key: string]: ColumnType};
    id: string;
    name: string;
    numberOfRows: number;
    target?: string | null;
}