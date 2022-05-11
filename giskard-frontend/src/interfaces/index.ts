export interface IUserProfileMinimal {
  id: number,
  user_id: string,
  display_name?: string
}

export interface IDataMetadata {
  feat_name: string,
  feat_type: string,
  feat_cat_values: string[]
}

export interface IModelMetadata {
  prediction_task: string,
  classification_labels: string[],
  classification_threshold: number
}
export interface RowDetails {
  index: number;
  item: any;
}