import type {FeatureType} from './../../domain/feature-type';

/**
 * Generated from ai.giskard.web.dto.DataUploadParamsDTO
 */
export interface DataUploadParamsDTO {
    featureTypes: {[key: string]: FeatureType};
    columnTypes: {[key: string]: string};
    name: string;
    projectKey: string;
    target: string;
}