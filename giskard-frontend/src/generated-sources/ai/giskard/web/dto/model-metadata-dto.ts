import type {ModelType} from './../../domain/ml/model-type';

/**
 * Generated from ai.giskard.web.dto.ModelMetadataDTO
 */
export interface ModelMetadataDTO {
    classificationLabels: string[];
    featureNames: string[];
    id: number;
    modelType: ModelType;
    threshold: number;
}