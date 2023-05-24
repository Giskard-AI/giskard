from giskard.core.core import SupportedModelTypes
from ..push import PerturbationPush
from .utils import slice_bounds
import numpy as np
from giskard.push import SupportedPerturbationType
from giskard.scanner.robustness.text_transformations import text_lowercase, \
    text_uppercase, \
    text_titlecase, \
    TextTypoTransformation, \
    TextPunctuationRemovalTransformation, \
    TextGenderTransformation
from giskard.ml_worker.testing.registry.transformation_function import TransformationFunction
import pandas as pd

text_transfo_list = [text_lowercase,
                     text_uppercase,
                     text_titlecase,
                     TextTypoTransformation,
                     TextPunctuationRemovalTransformation,
                     TextGenderTransformation]


def perturbation(model, ds, idrow):
    for feat, coltype in ds.column_types.items():
        perturbation_res = Perturbation(model, ds, idrow, feat, coltype)
        if perturbation_res.coltype == SupportedPerturbationType.NUMERIC and perturbation_res.passed:
            res = PerturbationPush(feature=feat, value=ds.df.iloc[idrow][feat],
                                   transformation_function=perturbation_res.transformation_function)
            return res

        if perturbation_res.coltype == SupportedPerturbationType.TEXT and perturbation_res.passed:
            res = PerturbationPush(feature=feat, value=ds.df.iloc[idrow][feat],
                                   text_perturbed=perturbation_res.text_perturbed,
                                   transformation_function=perturbation_res.transformation_function
                                   )
            return res


class Perturbation:
    model = None
    ds = None
    idrow = None
    feat = None
    coltype = None
    passed = None
    perturbation_value = None
    text_perturbed = None
    transformation_function = None

    def __init__(self, model, ds, idrow, feature, coltype):
        self.model = model
        self.ds = ds
        self.idrow = idrow
        self.feature = feature
        if coltype == "numeric":
            self.coltype = SupportedPerturbationType.NUMERIC
        elif coltype == "text":
            self.coltype = SupportedPerturbationType.TEXT
        self.transformation_function = list()
        self.text_perturbed = list()
        self._perturb_and_predict()

    def _perturb_and_predict(self):  # done at each step
        def mad(x):
            med = np.median(x)
            x = abs(x - med)
            mad = np.median(x)
            return mad

        ref_row = self.ds.df.iloc[[self.idrow]]
        row_perturbed = ref_row.copy()
        if self.coltype == SupportedPerturbationType.NUMERIC:
            mad = mad(self.ds.df[self.feature])
            ds_slice = self.ds.slice(lambda x: x.loc[x.index == self.idrow], row_level=False)
            t, row_perturbed[self.feature] = self._num_perturb(3 * mad, self.feature, ds_slice)
            self._generate_perturbation(ref_row, row_perturbed)
            if self.passed:
                self.transformation_function.append(t)

        elif self.coltype == SupportedPerturbationType.TEXT:
            for text_transformation in text_transfo_list:
                ds_slice = self.ds.slice(lambda x: x.loc[x.index == self.idrow], row_level=False)
                t, row_perturbed[self.feature] = self._text_perturb(text_transformation, self.feature, ds_slice)
                self._generate_perturbation(ref_row, row_perturbed)
                if self.passed:
                    self.text_perturbed.append(row_perturbed[self.feature])
                    self.transformation_function.append(t)
            if len(self.text_perturbed) > 0:
                self.passed = True

    def _generate_perturbation(self, ref_row, row_perturbed):
        if self.model.meta.model_type == SupportedModelTypes.CLASSIFICATION:
            ref_prob = self.model.model.predict(ref_row)
            probabilities = self.model.model.predict(row_perturbed)  # .reshape(1, -1)
            self.passed = ref_prob[0] != probabilities[0]
        elif self.model.meta.model_type == SupportedModelTypes.REGRESSION:
            ref_val = self.model.model.predict(ref_row.drop(columns=[self.ds.target]))
            new_val = self.model.model.predict(row_perturbed.drop(columns=[self.ds.target]))  # .reshape(1, -1)
            self.passed = (new_val - ref_val) / ref_val >= 0.2

    def _num_perturb(self, perturbation_value, col, ds_slice):
        t = NumTransformation(column=col, perturbation_value=perturbation_value)
        transformed = ds_slice.transform(t)
        transformed_num = transformed.df[self.feature].values
        return t, transformed_num

    def _text_perturb(self, transformation_function, col, ds_slice):
        t = transformation_function(column=col)
        transformed = ds_slice.transform(t)
        transformed_text = transformed.df[self.feature].values
        return t, str(transformed_text)


class NumTransformation(TransformationFunction):
    row_level = False
    name = "mad perturbation"

    def __init__(self, column, perturbation_value):
        self.column = column
        self.perturbation_value = perturbation_value

    def execute(self, data: pd.DataFrame):
        data = data.copy()
        data[self.column] = data[self.column].apply(lambda x: x + self.perturbation_value)
        return data
