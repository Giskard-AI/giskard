from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

import pandas as pd

from ..datasets import Dataset
from ..ml_worker.testing.registry.slicing_function import SlicingFunction
from ..ml_worker.testing.registry.transformation_function import TransformationFunction
from ..models.base import BaseModel
from ..slicing.slice import QueryBasedSliceFunction
from ..slicing.text_slicer import MetadataSliceFunction


class IssueLevel(Enum):
    MAJOR = "major"
    MEDIUM = "medium"
    MINOR = "minor"


@dataclass(frozen=True)
class IssueGroup:
    name: str
    description: str


class Issue:
    def __init__(
        self,
        model: BaseModel,
        dataset: Dataset,
        group: IssueGroup,
        level: IssueLevel = IssueLevel.MINOR,
        description: str = "",
        meta: Optional[dict] = None,
        transformation_fn: Optional[TransformationFunction] = None,
        slicing_fn: Optional[SlicingFunction] = None,
        importance: float = 0,
        examples: Optional[pd.DataFrame] = None,
        features: Optional[List[str]] = None,
        tests=None,
        taxonomy: List[str] = None,
    ):
        """Issue represents a single model vulnerability detected by Giskard.

        Parameters
        ----------
        model : BaseModel
            Model that was tested and on which the vulnerability was detected.
        dataset : Dataset
            Dataset used for vulnerability detection.
        group : IssueGroup
            Group of the issue, e.g. Robustness, Performance, etc.
        level : IssueLevel, optional
            Level or severity of the issue, by default IssueLevel.MINOR.
        description : str, optional
            Description of the issue in human language.
        meta : Optional[dict], optional
            Additional metadata about the issue.
        transformation_fn : Optional[TransformationFunction], optional
            Transformation function, used for vulnerabilities detected via metamorphic testing, for example with
            perturbations of the inputs.
        slicing_fn : Optional[SlicingFunction], optional
            Slicing function, used for vulnerabilities affecting a single data slice.
        importance : float, optional
            Arbitrary importance score of the issue, used for ordering.
        examples : Optional[pd.DataFrame], optional
            Examples of the vulnerability as a `pandas.DataFrame`.
        features : Optional[List[str]], optional
            List of features affected by the issue.
        tests : Optional[Union[dict, callable]], optional
            Either a dictionary of tests, keyed by name, or a callable that returns a dictionary of tests. Each test is
            a test function from the giskard library (or a custom test defined by the ``@test`` decorator).
            For example, ``{"Test that accuracy is good": giskard.testing.tests.test_accuracy()}``.
        taxonomy : Optional[str], optional
            List of taxonomy machine tags, in MISP format. A machine tag is composed of a namespace (MUST), a predicate
            (MUST) and an (OPTIONAL) value, like ``namespace:predicate:value``.
        """
        self.group = group
        self.model = model
        self.dataset = dataset
        self.level = level
        self.description_tpl = description
        self.meta = meta or dict()
        self.transformation_fn = transformation_fn
        self.slicing_fn = slicing_fn
        self.importance = importance
        self._examples = examples
        self._features = features
        self._tests = tests
        self.taxonomy = taxonomy or []

    def __repr__(self):
        return f"<{self.__class__.__name__} group='{self.group.name}' level='{self.level}'>"

    @property
    def is_major(self) -> bool:
        return self.level == IssueLevel.MAJOR

    @property
    def is_medium(self) -> bool:
        return self.level == IssueLevel.MEDIUM

    @property
    def is_minor(self) -> bool:
        return self.level == IssueLevel.MINOR

    @property
    def features(self) -> List[str]:
        if self._features is not None:
            return self._features

        if isinstance(self.slicing_fn, QueryBasedSliceFunction):
            return self.slicing_fn.query.columns()
        if isinstance(self.slicing_fn, MetadataSliceFunction):
            return [self.slicing_fn.feature]

        return self.model.meta.feature_names or self.dataset.columns.tolist()

    @property
    def description(self):
        return self.description_tpl.format(
            model=self.model,
            dataset=self.dataset,
            transformation_fn=self.transformation_fn,
            slicing_fn=self.slicing_fn,
            level=self.level.value,
            **self.meta,
        )

    def examples(self, n=3) -> pd.DataFrame:
        if self._examples is not None:
            return self._examples.head(n)
        return pd.DataFrame()

    def add_examples(self, examples: pd.DataFrame):
        if self._examples is None:
            self._examples = examples
        else:
            self._examples = pd.concat([self._examples, examples])

    def generate_tests(self, with_names=False) -> list:
        tests = self._tests(self) if callable(self._tests) else self._tests

        if tests is None:
            return []

        if with_names:
            return list(zip(tests.values(), tests.keys()))
        return list(tests.values())


Robustness = IssueGroup(
    "Robustness",
    description="""
Your model seems to be sensitive to small perturbations in the input data. These perturbations can include adding typos,
changing word order, or turning text into uppercase or lowercase. This happens when:

- There is not enough diversity in the training data
- Overreliance on spurious correlations like the presence of specific word
- Use of complex models with large number of parameters that tend to overfit the training data

To learn more about causes and solutions, check our [guide on robustness issues](https://docs.giskard.ai/en/latest/getting-started/key_vulnerabilities/robustness/index.html).
""",
)

Performance = IssueGroup(
    "Performance",
    description="""
We found some data slices in your dataset on which your model performance is lower than average. Performance bias may
happen for different reasons:

- Not enough examples in the low-performing data slice in the training set
- Wrong labels in the training set in the low-performing data slice
- Drift between your training set and test set

To learn more about causes and solutions, check our [guide on performance bias.](https://docs.giskard.ai/en/latest/getting-started/key_vulnerabilities/performance_bias/index.html)
""",
)

Overconfidence = IssueGroup(
    name="Overconfidence",
    description="""
We found some data slices in your dataset containing significant number of overconfident predictions. Overconfident predictions are rows that are incorrect but are predicted with high probabilities or confidence scores. This happens when:

- There are not enough examples in the overconfident data slice in the training set
- Wrongly labeled examples in the training set in the overconfident data slice
- For imbalanced datasets, the model may assign high probabilities to predictions of the majority class

To learn more about causes and solutions, check our [guide on overconfidence issues.](https://docs.giskard.ai/en/latest/getting-started/key_vulnerabilities/overconfidence/index.html)
""",
)

Underconfidence = IssueGroup(
    name="Underconfidence",
    description="""
We found some data slices in your dataset containing significant number of underconfident predictions. Underconfident predictions refer to situations where the predicted label has a probability that is very close to the probability of the next highest probability label. This happens when:

- There are not enough examples in the training set for the underconfident data slice
- The model is too simple and struggles to capture the complexity of the underlying data
- The underconfident data slice contains inherent noise or overlapping feature distributions

To learn more about causes and solutions, check our [guide on underconfidence issues.](https://docs.giskard.ai/en/latest/getting-started/key_vulnerabilities/underconfidence/index.html)
""",
)

Ethical = IssueGroup(
    name="Ethical",
    description="""
Your model seems to be sensitive to gender, ethnic, or religion based perturbations in the input data. These perturbations can include switching some words from feminine to masculine, countries or nationalities. This happens when:

- Underrepresentation of certain demographic groups in the training data
- Data is reflecting some structural biases and societal prejudices
- Use of complex models with large number of parameters that tend to overfit the training data

To learn more about causes and solutions, check our [guide on unethical behaviour.](https://docs.giskard.ai/en/latest/getting-started/key_vulnerabilities/ethics/index.html)""",
)

DataLeakage = IssueGroup(
    name="Data Leakage",
    description="""
Your model seems to present some data leakage. The model provides different results depending on whether it is computing on a single data point or the entire dataset. This happens when:

- Preprocessing steps, such as scaling, missing value imputation, or outlier handling, are fitted inside the prediction pipeline
- Train-test splitting is done after preprocessing or feature selection

To learn more about causes and solutions, check our [guide on data leakage.](https://docs.giskard.ai/en/latest/getting-started/key_vulnerabilities/data_leakage/index.html)""",
)

Stochasticity = IssueGroup(
    name="Stochasticity",
    description="""
Your model seems to present some stochastic behaviour. The model provides different results at each execution. This may happen when some stochastic training process is included in the prediction pipeline.

To learn more about causes and solutions, check our [guide on stochasticity issues.](https://docs.giskard.ai/en/latest/getting-started/key_vulnerabilities/stochasticity/index.html)""",
)

SpuriousCorrelation = IssueGroup(
    name="Spurious Correlation",
    description="""
We found some potential spurious correlations between your data and the model predictions. Some data slices are highly correlated with your predictions. This happens when:

- Data leakage: one of the feature is indirectly linked with the target variable
- Overfitting: the model learns specific noisy patterns of the training data, including coincidental correlations that are not causal
- Data noise: the training set contains anomalies that are unrelated to the underlying problem (data collection, measurement biases, data preprocessing issues, etc.)

To learn more about causes and solutions, check our [guide on spurious correlation.](https://docs.giskard.ai/en/latest/getting-started/key_vulnerabilities/spurious/index.html)""",
)

Harmfulness = IssueGroup(
    name="Harmfulness", description="We found that your model can generate harmful or toxic content."
)

Stereotypes = IssueGroup(
    name="Stereotypes", description="Your model seems to exhibit social stereotypes about genders or minorities."
)

Hallucination = IssueGroup(
    name="Hallucination and Misinformation",
    description="We detected that the model can generate hallucinated, non-factual, or incoherent outputs. Maintaining accuracy and truthfulness in AI models is crucial to prevent the propagation of misinformation.",
)

SensitiveInformationDisclosure = IssueGroup(
    name="Sensitive Information Disclosure",
    description="We detected that the model may leak sensitive or confidential information in its reponses. Protecting user privacy and data security is paramount when using AI models.",
)

OutputFormatting = IssueGroup(
    name="Output Formatting",
    description="We detected that the model may require a specific format for its output, but this format was not always respected. Model output should be verified to ensure that its format is consistent with the downstream application requirements.",
)
