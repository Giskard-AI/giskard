import type {ColumnMeaning} from './../../domain/column-meaning';

/**
 * Generated from ai.giskard.web.dto.DataUploadParamsDTO
 */
export interface DataUploadParamsDTO {
    columnTypes: {[key: string]: string};
    columnMeanings: {[key: string]: ColumnMeaning};
    name: string;
    projectKey: string;
    target: string;
}