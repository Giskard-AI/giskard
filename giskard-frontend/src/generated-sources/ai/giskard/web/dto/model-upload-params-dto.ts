import type {ModelLanguage} from './../../domain/ml/model-language';
import type {ModelType} from './../../domain/ml/model-type';

/**
 * Generated from ai.giskard.web.dto.ModelUploadParamsDTO
 */
export interface ModelUploadParamsDTO {
    classificationLabels: string;
    features: string;
    language: ModelLanguage;
    languageVersion: string;
    modelType: ModelType;
    name: string;
    projectKey: string;
    target: string;
    threshold: number;
}