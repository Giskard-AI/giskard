import type {ColumnType} from './../../../domain/column-type';
import type {ProjectDTO} from './project-dto';

/**
 * Generated from ai.giskard.web.dto.ml.DatasetDTO
 */
export interface DatasetDTO {
    categoryFeatures: {[key: string]: string[]};
    columnDtypes: {[key: string]: string};
    columnTypes: {[key: string]: ColumnType};
    compressedSizeBytes: number;
    createdDate: any /* TODO: Missing translation of java.time.Instant */;
    id: string;
    name: string;
    numberOfRows: number;
    originalSizeBytes: number;
    project: ProjectDTO;
    target?: string | null;
}