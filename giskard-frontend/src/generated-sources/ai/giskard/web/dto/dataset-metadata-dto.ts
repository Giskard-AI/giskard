import type {FeatureType} from './../../domain/feature-type';

/**
 * Generated from ai.giskard.web.dto.DatasetMetadataDTO
 */
export interface DatasetMetadataDTO {
    columnTypes?: {[key: string]: string} | null;
    featureTypes: {[key: string]: FeatureType};
    id: number;
    target?: string | null;
}