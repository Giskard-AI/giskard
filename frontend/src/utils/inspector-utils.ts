import { ModelDTO, ModelDTOModelTypeEnum } from '@/generated/client';
import { types } from 'sass';
import Error = types.Error;

export enum InspectorFeature {
  EXPLANATION
}

const FEATURES_PER_MODELS: { [type in ModelDTOModelTypeEnum]: InspectorFeature[] } = {
  [ModelDTOModelTypeEnum.Classification]: [InspectorFeature.EXPLANATION],
  [ModelDTOModelTypeEnum.Regression]: [InspectorFeature.EXPLANATION],
  [ModelDTOModelTypeEnum.TextGeneration]: []
};

export class InspectorUtils {

  private InspectorUtils() {
    throw new Error('Utils class');
  }

  static hasFeature(feature: InspectorFeature, model?: ModelDTO): boolean {
    return model?.modelType !== undefined && FEATURES_PER_MODELS[model.modelType].includes(feature);
  }

}
