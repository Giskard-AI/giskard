import type {FeatureType} from './../../domain/feature-type';

/**
 * Generated from ai.giskard.web.dto.DatasetMetadataDTO
 */
export interface DatasetMetadataDTO {
    businessNames?: {[key: string]: string} | null;
    categoryBusinessNames?: {[key: string]: {[key: string]: string}} | null;
    columnTypes?: {[key: string]: string} | null;
    featureTypes: {[key: string]: FeatureType};
    id: string;
    name: string;
    target?: string | null;
}