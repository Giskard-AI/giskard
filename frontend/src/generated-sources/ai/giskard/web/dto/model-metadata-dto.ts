import type {ModelType} from './../../domain/ml/model-type';

/**
 * Generated from ai.giskard.web.dto.ModelMetadataDTO
 */
export interface ModelMetadataDTO {
    classificationLabels: string[];
    featureNames: string[];
    id: string;
    modelType: ModelType;
    threshold: number;
}