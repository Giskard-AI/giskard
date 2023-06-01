import type {ModelLanguage} from './../../domain/ml/model-language';

/**
 * Generated from ai.giskard.web.dto.ModelUploadParamsDTO
 */
export interface ModelUploadParamsDTO {
    classificationLabels: string[];
    featureNames: string[];
    language: ModelLanguage;
    languageVersion: string;
    modelType: string;
    name: string;
    projectKey: string;
    threshold: number;
}