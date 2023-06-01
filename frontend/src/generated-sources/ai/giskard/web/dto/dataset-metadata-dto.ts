import type {ColumnMeaning} from './../../domain/column-meaning';

/**
 * Generated from ai.giskard.web.dto.DatasetMetadataDTO
 */
export interface DatasetMetadataDTO {
    columnMeanings: {[key: string]: ColumnMeaning};
    columnTypes?: {[key: string]: string} | null;
    id: string;
    name: string;
    target?: string | null;
}