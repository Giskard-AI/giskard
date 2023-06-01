import type {FeatureType} from './../../../domain/feature-type';
import type {ProjectDTO} from './project-dto';

/**
 * Generated from ai.giskard.web.dto.ml.DatasetDTO
 */
export interface DatasetDTO {
    columnTypes: {[key: string]: string};
    compressedSizeBytes: number;
    createdDate: any /* TODO: Missing translation of java.time.Instant */;
    featureTypes: {[key: string]: FeatureType};
    id: string;
    name: string;
    originalSizeBytes: number;
    project: ProjectDTO;
    target?: string | null;
}