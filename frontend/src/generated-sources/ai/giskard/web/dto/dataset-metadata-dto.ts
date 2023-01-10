import type {ColumnMeaning} from './../../domain/column-meaning';

/**
 * Generated from ai.giskard.web.dto.DatasetMetadataDTO
 */
export interface DatasetMetadataDTO {
    columnTypes?: {[key: string]: string} | null;
    columnMeanings: {[key: string]: ColumnMeaning};
    id: string;
    name: string;
    target?: string | null;
}