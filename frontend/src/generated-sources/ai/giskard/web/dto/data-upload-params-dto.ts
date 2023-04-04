import type {ColumnType} from './../../domain/column-type';

/**
 * Generated from ai.giskard.web.dto.DataUploadParamsDTO
 */
export interface DataUploadParamsDTO {
    columnDtypes: {[key: string]: string};
    columnTypes: {[key: string]: ColumnType};
    name: string;
    projectKey: string;
    target: string;
}