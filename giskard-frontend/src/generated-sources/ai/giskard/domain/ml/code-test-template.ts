import type {ModelType} from './model-type';

/**
 * Generated from ai.giskard.domain.ml.CodeTestTemplate
 */
export interface CodeTestTemplate {
    code: string;
    enabled: boolean;
    hint: string;
    id: string;
    isGroundTruthRequired: boolean;
    isMultipleDatasets: boolean;
    modelTypes: ModelType[];
    title: string;
}