import type {ModelType} from './../../domain/ml/model-type';

/**
 * Generated from ai.giskard.web.dto.ModelMetadataDTO
 */
export interface ModelMetadataDTO {
    classificationLabels: string[];
    features: {[key: string]: string};
    id: number;
    modelType: ModelType;
    target: string;
    threshold: number;
}