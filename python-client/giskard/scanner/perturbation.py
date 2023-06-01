from typing import Optional
from ..models.base import BaseModel
from ..datasets.base import Dataset
from giskard.scanner.unit_perturbation import TransformationGenerator
from giskard.ml_worker.testing.tests.metamorphic import test_metamorphic_invariance


class RobustnessScan:
    def __init__(self, model: Optional[BaseModel] = None, dataset: Optional[Dataset] = None):
        self.model = model
        self.dataset = dataset

    def run(
            self,
            model: Optional[BaseModel] = None,
            dataset: Optional[Dataset] = None,
    ):
        model = model or self.model
        dataset = dataset or self.dataset

        if model is None:
            raise ValueError("You need to provide a model to test.")
        if dataset is None:
            raise ValueError("You need to provide an evaluation dataset.")

        test_results = []
        transformation = TransformationGenerator(model=model, dataset=dataset)
        for feature, feature_type in dataset.column_types.items():
            if feature_type == "numeric":
                transformation_function = transformation.generate_std_transformation(feature)

                test_result = test_metamorphic_invariance(
                    model=model,
                    dataset=dataset,
                    transformation_function=transformation_function,
                    threshold=0.8
                ).execute()

                if not test_result.passed:
                    test_results.append(("passed", feature, test_result.metric))
                else:
                    test_results.append(("failed", feature, test_result.metric))

            if feature_type == "text":
                transformation_function = transformation.text_transformation(feature)
                test_result = test_metamorphic_invariance(
                    model=model,
                    dataset=dataset,
                    transformation_function=transformation_function,
                    threshold=0.8
                ).execute()
                if not test_result.passed:
                    test_results.append(("passed", feature, test_result.metric))
                else:
                    test_results.append(("failed", feature, test_result.metric))


        return test_results
