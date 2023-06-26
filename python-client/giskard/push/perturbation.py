import numpy as np
import pandas as pd

from giskard.core.core import SupportedModelTypes
from giskard.ml_worker.testing.registry.transformation_function import TransformationFunction
from giskard.push import SupportedPerturbationType
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


def create_perturbation_push(model, ds, idrow):
    for feat, coltype in ds.column_types.items():
        perturbation_res = Perturbation(model, ds, idrow, feat, coltype)
        if perturbation_res.coltype == SupportedPerturbationType.NUMERIC and perturbation_res.passed:
            res = PerturbationPush(
                feature=feat,
                value=ds.df.iloc[idrow][feat],
                transformation_function=perturbation_res.transformation_function,
            )
            return res

        if perturbation_res.coltype == SupportedPerturbationType.TEXT and perturbation_res.passed:
            res = PerturbationPush(
                feature=feat,
                value=ds.df.iloc[idrow][feat],
                text_perturbed=perturbation_res.text_perturbed,
                transformation_function=perturbation_res.transformation_function,
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

    def _perturb_and_predict(self):
        def mad(x):
            med = np.median(x)
            x = abs(x - med)
            mad = np.median(x)
            return mad

        idrow = self.idrow
        ds_slice = self.ds.slice(lambda df: df.loc[df.index == idrow], row_level=False)

        row_perturbed = ds_slice.copy()
        if self.coltype == SupportedPerturbationType.NUMERIC:
            mad = mad(self.ds.df[self.feature])

            t, row_perturbed = self._num_perturb(3 * mad, self.feature, ds_slice)
            self._generate_perturbation(ds_slice, row_perturbed)

            if self.passed:
                self.transformation_function.append(t)

        elif self.coltype == SupportedPerturbationType.TEXT:
            for text_transformation in text_transfo_list:
                t, row_perturbed = self._text_perturb(text_transformation, self.feature, ds_slice)
                self._generate_perturbation(ds_slice, row_perturbed)

                if self.passed:
                    self.text_perturbed.append(row_perturbed.df[self.feature])
                    self.transformation_function.append(t)

            if len(self.text_perturbed) > 0:
                self.passed = True

    def _generate_perturbation(self, ref_row, row_perturbed):
        if self.model.meta.model_type == SupportedModelTypes.CLASSIFICATION:
            ref_prob = self.model.predict(ref_row).prediction[0]
            probabilities = self.model.predict(row_perturbed).prediction[0]
            self.passed = ref_prob[0] != probabilities[0]
        elif self.model.meta.model_type == SupportedModelTypes.REGRESSION:
            ref_val = self.model.predict(ref_row).prediction[0]
            new_val = self.model.predict(row_perturbed).prediction[0]
            self.passed = (new_val - ref_val) / ref_val >= 0.2

    def _num_perturb(self, perturbation_value, col, ds_slice):
        t = NumTransformation(column=col, perturbation_value=perturbation_value)
        transformed = ds_slice.transform(t)
        return t, transformed

    def _text_perturb(self, transformation_function, col, ds_slice):
        t = transformation_function(column=col)
        transformed = ds_slice.transform(t)
        return t, transformed


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
