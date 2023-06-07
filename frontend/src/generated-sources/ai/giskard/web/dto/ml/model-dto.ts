import type {ModelLanguage} from './../../../domain/ml/model-language';
import type {ModelType} from './../../../domain/ml/model-type';
import type {ProjectDTO} from './project-dto';

/**
 * Generated from ai.giskard.web.dto.ml.ModelDTO
 */
export interface ModelDTO {
    classificationLabels: string[];
    classificationLabelsDtype: string;
    createdDate: any /* TODO: Missing translation of java.time.Instant */;
    featureNames?: string[] | null;
    id: string;
    language: ModelLanguage;
    languageVersion: string;
    modelType: ModelType;
    name: string;
    project: ProjectDTO;
    size: number;
    threshold: number;
}