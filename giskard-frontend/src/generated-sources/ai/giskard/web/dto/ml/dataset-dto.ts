import type {FeatureType} from './../../../domain/feature-type';
import type {_FileDTO} from './file-dto';

/**
 * Generated from ai.giskard.web.dto.ml.DatasetDTO
 */
export interface DatasetDTO extends _FileDTO {
    featureTypes: {[key: string]: FeatureType};
    target: string;
}