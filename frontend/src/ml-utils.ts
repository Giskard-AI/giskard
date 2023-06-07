import {ModelType} from '@/generated-sources';

export function isClassification(modelType: ModelType) {
    return modelType === ModelType.CLASSIFICATION;
}