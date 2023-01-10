import type {ColumnMeaning} from './../../../domain/column-meaning';
import type {ProjectDTO} from './project-dto';

/**
 * Generated from ai.giskard.web.dto.ml.DatasetDTO
 */
export interface DatasetDTO {
    columnTypes: {[key: string]: string};
    compressedSizeBytes: number;
    createdDate: any /* TODO: Missing translation of java.time.Instant */;
    columnMeanings: {[key: string]: ColumnMeaning};
    id: string;
    name: string;
    originalSizeBytes: number;
    project: ProjectDTO;
    target?: string | null;
}