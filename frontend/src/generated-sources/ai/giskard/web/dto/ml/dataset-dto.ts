import type {ColumnMeaning} from './../../../domain/column-meaning';
import type {ProjectDTO} from './project-dto';

/**
 * Generated from ai.giskard.web.dto.ml.DatasetDTO
 */
export interface DatasetDTO {
    columnMeanings: {[key: string]: ColumnMeaning};
    columnTypes: {[key: string]: string};
    compressedSizeBytes: number;
    createdDate: any /* TODO: Missing translation of java.time.Instant */;
    id: string;
    name: string;
    originalSizeBytes: number;
    project: ProjectDTO;
    target?: string | null;
}