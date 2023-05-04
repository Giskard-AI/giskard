from giskard.core.core import SupportedModelTypes
from ..push import Push, Perturbation
from .utils import slice_bounds
import numpy as np

from giskard.scanner.robustness.text_transformations import text_lowercase, \
    text_uppercase, \
    text_titlecase, \
    TextTypoTransformation, \
    TextPunctuationRemovalTransformation, \
    TextGenderTransformation

text_transfo_list = (text_lowercase,
                     text_uppercase,
                     text_titlecase,
                     TextTypoTransformation,
                     TextPunctuationRemovalTransformation,
                     TextGenderTransformation)


def perturbation(model, ds, idrow):
    for feat, coltype in ds.column_types.items():
        perturbation_res_list = _perturb_and_predict(model, ds, idrow, feat, coltype)
        for perturbation_res in perturbation_res_list:
            if coltype == "numeric" and perturbation_res.passed:
                bounds = slice_bounds(feature=feat, value=ds.df.iloc[idrow][feat], ds=ds)
                res = Push(push_type="perturbation", feature=feat, value=ds.df.iloc[idrow][feat],
                           bounds=bounds,
                           perturbation_value=perturbation_res.perturbation_value)
                yield res

            # if coltype == "text" and _perturb_and_predict(model, ds, idrow, feat, coltype):
            #     bounds = slice_bounds(feature=feat, value=ds.df.iloc[idrow][feat], ds=ds)
            #     res = Push(push_type="perturbation", feature=feat, value=ds.df.iloc[idrow][feat],
            #                bounds=bounds,
            #                perturbation_value=perturbation_res.perturbation_value)

            # {
            #     "sentence": "A small variation of the text makes the prediction change, do you want to "
            #                 "check if this unrobust behavior generalizes to the whole dataset ?",
            #     "action": "Test",
            #     "value": str(ds.df.iloc[idrow][feat]),
            #     "key": str(feat),
            # # }
            #
            # yield res


def _perturb_and_predict(model, ds, idrow, feature, coltype):  # done at each step
    def mad(x):
        med = np.median(x)
        x = abs(x - med)
        mad = np.median(x)
        return mad

    ref_row = ds.df.iloc[[idrow]]
    row_perturbed = ref_row.copy()
    perturbation_val = None

    perturbations = []
    if coltype == "numeric":
        mad = mad(ds.df[feature])
        row_perturbed[feature] = _num_perturb(row_perturbed[feature], mad)
        perturbation_val = mad
        perturbations.append(_generate_perturbation(model, ds, ref_row, row_perturbed, perturbation_val))
    elif coltype == "text":
        for text_transformation in text_transfo_list:
            ds_slice = ds.slice(lambda df: df.loc[idrow], row_level=False)
            row_perturbed[feature] = _text_perturb(text_transformation, feature, ds_slice)
            perturbation_val = None  # @TODO: Add text support
            perturbations.append(_generate_perturbation(model, ds, ref_row, row_perturbed, perturbation_val))
    return perturbations


def _generate_perturbation(model, ds, ref_row, row_perturbed, perturbation_val):
    if model.meta.model_type == SupportedModelTypes.CLASSIFICATION:
        ref_prob = model.model.predict(ref_row)
        probabilities = model.model.predict(row_perturbed)  # .reshape(1, -1)
        return Perturbation(passed=ref_prob[0] != probabilities[0], perturbation_value=perturbation_val)
    elif model.meta.model_type == SupportedModelTypes.REGRESSION:
        ref_val = model.model.predict(ref_row.drop(columns=[ds.target]))
        new_val = model.model.predict(row_perturbed.drop(columns=[ds.target]))  # .reshape(1, -1)
        return Perturbation(passed=(new_val - ref_val) / ref_val >= 0.2, perturbation_value=perturbation_val)


def _num_perturb(val, mad):
    return val + 3 * mad  # 1.2  # 20% perturbation


def _text_perturb(val):
    # Define the augmenter
    aug = naw.SynonymAug()  # .SynonymAug()
    # Augment the text
    aug_text = aug.augment(data=val)
    return aug_text
def perturbation(model, ds, idrow):
    for feat, coltype in ds.column_types.items():
        perturbation_res = _perturb_and_predict(model, ds, idrow, feat, coltype)
        if coltype == "numeric" and perturbation_res.passed:
            res = Push(push_type="perturbation", feature=feat, value=ds.df.iloc[idrow][feat],
                       perturbation_value=perturbation_res.perturbation_value)
            yield res

        # if coltype == "text" and _perturb_and_predict(model, ds, idrow, feat, coltype):
        #     res = [
        #         {
        #             "sentence": "A small variation of the text makes the prediction change, do you want to "
        #                         "check if this unrobust behavior generalizes to the whole dataset ?",
        #             "action": "Test",
        #             "value": str(ds.df.iloc[idrow][feat]),
        #             "key": str(feat),
        #         }
        #     ]
        #     return res


def _perturb_and_predict(model, ds, idrow, feature, coltype):  # done at each step
    ref_row = ds.df.iloc[[idrow]]
    row_perturbed = ref_row.copy()
    perturbation_val = None
    if coltype == "numeric":
        mad = ds.df[feature].mad()
        row_perturbed[feature] = _num_perturb(row_perturbed[feature], mad)
        perturbation_val = mad
    if coltype == "text":
        row_perturbed[feature] = _text_perturb(str(row_perturbed[feature]))
        perturbation_val = None  # @TODO: Add text support
    # print(row_perturbed[feature])
    # Predict probabilities for the perturbed input row using the given model
    if model.meta.model_type == SupportedModelTypes.CLASSIFICATION:
        ref_prob = model.clf.predict(ref_row)
        probabilities = model.clf.predict(row_perturbed)  # .reshape(1, -1)
        return Perturbation(passed=ref_prob[0] != probabilities[0], perturbation_value=perturbation_val)
    if model.meta.model_type == SupportedModelTypes.REGRESSION:
        ref_val = model.clf.predict(ref_row.drop(columns=[ds.target]))
        new_val = model.clf.predict(row_perturbed.drop(columns=[ds.target]))  # .reshape(1, -1)
        return Perturbation(passed=(new_val - ref_val) / ref_val >= 0.2, perturbation_value=perturbation_val)


def _num_perturb(val, mad):
    return val + mad  # 1.2  # 20% perturbation


def _text_perturb(val):
    # Define the augmenter
    aug = naw.SynonymAug()  # .SynonymAug()
    # Augment the text
    aug_text = aug.augment(data=val)
    return aug_text
