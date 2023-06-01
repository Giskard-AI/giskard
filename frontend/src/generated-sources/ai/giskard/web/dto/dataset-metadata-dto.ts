import type {FeatureType} from './../../domain/feature-type';

/**
 * Generated from ai.giskard.web.dto.DatasetMetadataDTO
 */
export interface DatasetMetadataDTO {
    featureTypes: {[key: string]: FeatureType};
    columnTypes?: {[key: string]: string} | null;
    id: string;
    name: string;
    target?: string | null;
}