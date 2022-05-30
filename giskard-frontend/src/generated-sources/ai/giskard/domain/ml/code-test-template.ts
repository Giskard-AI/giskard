import type {ModelType} from './model-type';

/**
 * Generated from ai.giskard.domain.ml.CodeTestTemplate
 */
export interface CodeTestTemplate {
    code: string;
    hint: string;
    id: string;
    modelTypes: ModelType[];
    title: string;
}