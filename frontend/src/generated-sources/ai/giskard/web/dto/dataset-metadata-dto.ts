import type {ColumnType} from './../../domain/column-type';

/**
 * Generated from ai.giskard.web.dto.DatasetMetadataDTO
 */
export interface DatasetMetadataDTO {
    categoryFeatures: {[key: string]: string[]};
    columnDtypes?: {[key: string]: string} | null;
    columnTypes: {[key: string]: ColumnType};
    id: any /* TODO: Missing translation of java.util.UUID */;
    name: string;
    numberOfRows: number;
    target?: string | null;
}