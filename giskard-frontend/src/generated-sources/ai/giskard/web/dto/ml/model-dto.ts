import type {ModelLanguage} from './../../../domain/ml/model-language';
import type {ModelType} from './../../../domain/ml/model-type';
import type {_FileDTO} from './file-dto';

/**
 * Generated from ai.giskard.web.dto.ml.ModelDTO
 */
export interface ModelDTO extends _FileDTO {
    classificationLabels: string;
    features: string;
    language: ModelLanguage;
    languageVersion: string;
    modelType: ModelType;
    requirementsFileName: string;
    target: string;
    threshold: number;
}