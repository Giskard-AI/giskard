from typing import Optional
from ..models.base import BaseModel
from ..datasets.base import Dataset
from giskard.scanner.unit_perturbation import df_std, generate_std_transfo
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
        for feature, feature_type in dataset.column_types.items():
            if feature_type == "numerical":
                std = df_std(dataset=dataset, feature=feature)
                numerical_perturbation = generate_std_transfo(std)
                test_results.append(
                    test_metamorphic_invariance(
                        model=model,
                        dataset=dataset,
                        transformation_function=numerical_perturbation,
                    )
                )

        return test_results
