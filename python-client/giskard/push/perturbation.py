import pandas as pd

from giskard.core.core import SupportedModelTypes
from giskard.datasets.base import Dataset
from giskard.ml_worker.testing.functions.transformation import mad_transformation
from giskard.models.base.model import BaseModel
from giskard.push.utils import (
    SupportedPerturbationType,
    TransformationInfo,
    coltype_to_supported_perturbation_type,
    compute_mad,
)
from giskard.scanner.robustness.text_transformations import (
    TextGenderTransformation,
    TextLowercase,
    TextPunctuationRemovalTransformation,
    TextTitleCase,
    TextTypoTransformation,
    TextUppercase,
)

from ..push import PerturbationPush

text_transfo_list = [
    TextLowercase,
    TextUppercase,
    TextTitleCase,
    TextTypoTransformation,
    TextPunctuationRemovalTransformation,
    TextGenderTransformation,
]


def create_perturbation_push(model, ds: Dataset, df: pd.DataFrame):
    for feat, coltype in ds.column_types.items():
        coltype = coltype_to_supported_perturbation_type(coltype)
        transformation_info = apply_perturbation(model, ds, df, feat, coltype)
        value = df.iloc[0][feat]
        if transformation_info is not None:
            return PerturbationPush(
                feature=feat,
                value=value,
                transformation_info=transformation_info,
            )


def apply_perturbation(model, ds, df, feature, coltype):
    transformation_function = list()
    value_perturbed = list()
    passed = False
    # Create a slice of the dataset with only the row to perturb
    ds_slice = Dataset(df=df, target=ds.target, column_types=ds.column_types.copy(), validation=False)

    # Create a copy of the slice to apply the transformation
    ds_slice_copy = ds_slice.copy()

    # Apply the transformation
    if coltype == SupportedPerturbationType.NUMERIC:
        # Compute the MAD of the column
        mad = compute_mad(ds.df[feature])
        value_added = 2 * mad
        reduce_value_added = True
        passed_at_leat_once = False
        while reduce_value_added:
            if value_added <= ds.df[feature].max():
                # Create the transformation
                t = mad_transformation(column_name=feature, value_added=value_added)

                # Transform the slice
                transformed = ds_slice_copy.transform(t)

                # Generate the perturbation
                passed = check_after_perturbation(model, ds_slice, transformed)
                if passed:
                    passed_at_leat_once = True
                    value_perturbed.append(transformed.df[feature].values.item(0))
                    transformation_function.append(t)
                    value_added /= 1.5
                elif (not passed) and passed_at_leat_once:
                    reduce_value_added = False
                    passed = True
                else:
                    reduce_value_added = False

    elif coltype == SupportedPerturbationType.TEXT:
        # Iterate over the possible text transformations
        for text_transformation in text_transfo_list:
            # Create the transformation
            t = text_transformation(column=feature)

            # Transform the slice
            transformed = ds_slice_copy.transform(t)

            # Generate the perturbation
            passed = check_after_perturbation(model, ds_slice, transformed)

            if passed:
                value_perturbed.append(transformed.df[feature].values.item(0))
                transformation_function.append(t)

        if len(value_perturbed) > 0:
            passed = True

    value_perturbed.reverse()
    transformation_function.reverse()
    return (
        TransformationInfo(value_perturbed=value_perturbed, transformation_functions=transformation_function)
        if passed
        else None
    )


def check_after_perturbation(model: BaseModel, ref_row: Dataset, row_perturbed: Dataset):
    if model.meta.model_type == SupportedModelTypes.CLASSIFICATION:
        # Compute the probability of the reference row
        ref_pred = model.predict(ref_row).prediction[0]
        # Compute the probability of the perturbed row
        pred = model.predict(row_perturbed).prediction[0]
        # Check if the probability of the reference row is different from the probability of the perturbed row
        passed = ref_pred != pred
        return passed

    elif model.meta.model_type == SupportedModelTypes.REGRESSION:
        # Compute the prediction of the reference row
        ref_val = model.predict(ref_row).prediction[0]
        # Compute the prediction of the perturbed row
        new_val = model.predict(row_perturbed).prediction[0]
        # Check if the prediction of the reference row is different from the prediction of the perturbed row
        passed = (new_val - ref_val) / ref_val >= 0.2
        return passed
