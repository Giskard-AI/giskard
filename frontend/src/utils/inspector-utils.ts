import { ModelDTO, ModelDTOModelTypeEnum } from '@/generated/client';

export enum InspectorFeature {
    EXPLANATION, PREDICTION_RESULT, GENERATION_RESULT
}

const FEATURES_PER_MODELS: { [type in ModelDTOModelTypeEnum]: InspectorFeature[] } = {
    [ModelDTOModelTypeEnum.Classification]: [InspectorFeature.PREDICTION_RESULT, InspectorFeature.EXPLANATION],
    [ModelDTOModelTypeEnum.Regression]: [InspectorFeature.PREDICTION_RESULT, InspectorFeature.EXPLANATION],
    [ModelDTOModelTypeEnum.TextGeneration]: [InspectorFeature.GENERATION_RESULT]
};

export class InspectorUtils {

  private InspectorUtils() {
    throw new Error('Utils class');
  }

  static hasFeature(feature: InspectorFeature, model?: ModelDTO): boolean {
    return model?.modelType !== undefined && FEATURES_PER_MODELS[model.modelType].includes(feature);
  }

}
