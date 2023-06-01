import type {ColumnMeaning} from './../../domain/column-meaning';

/**
 * Generated from ai.giskard.web.dto.DataUploadParamsDTO
 */
export interface DataUploadParamsDTO {
    columnMeanings: {[key: string]: ColumnMeaning};
    columnTypes: {[key: string]: string};
    name: string;
    projectKey: string;
    target: string;
}