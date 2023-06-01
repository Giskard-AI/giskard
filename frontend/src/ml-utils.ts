import { ModelType } from '@/generated-sources';

export function isClassification(modelType: ModelType) {
    return modelType === ModelType.BINARY_CLASSIFICATION || modelType === ModelType.MULTICLASS_CLASSIFICATION;
}