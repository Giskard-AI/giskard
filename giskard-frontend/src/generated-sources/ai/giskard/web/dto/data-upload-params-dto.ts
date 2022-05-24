import type {FeatureType} from './../../domain/feature-type';

/**
 * Generated from ai.giskard.web.dto.DataUploadParamsDTO
 */
export interface DataUploadParamsDTO {
    featureTypes: {[key: string]: FeatureType};
    name: string;
    projectKey: string;
    target: string;
}