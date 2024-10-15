from typing import Any, List, Optional

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

import pandas as pd

from ..core.validation import configured_validate_arguments
from ..datasets import Dataset
from ..models.base import BaseModel
from ..registry.slicing_function import SlicingFunction
from ..registry.transformation_function import TransformationFunction
from ..slicing.slice import QueryBasedSliceFunction
from ..slicing.text_slicer import MetadataSliceFunction


class IssueLevel(str, Enum):
    MAJOR = "major"
    MEDIUM = "medium"
    MINOR = "minor"


@dataclass(frozen=True)
class IssueGroup:
    name: str
    description: str


class ScanExamples(ABC):
    """
    Abstract class to manage examples from different data types,
    so that they can be displayed in a scan report.

    Methods
    -------
        extend(examples: Any):
            Abstract method to add examples
        head(n: int):
            Abstract method that should give access to first n examples
        to_html():
            Abstract method to render html content to display examples
    """

    @abstractmethod
    def extend(self, examples: Any):
        ...

    @abstractmethod
    def head(self, n: int):
        ...

    @abstractmethod
    def to_html(self):
        ...


class DataFrameScanExamples(ScanExamples):
    """
    ScanExamples class to manage examples from pandas dataframes
    """

    @configured_validate_arguments
    def __init__(self, examples: Optional[pd.DataFrame] = None):
        self.examples = pd.DataFrame() if examples is None else examples

    @configured_validate_arguments
    def extend(self, examples: pd.DataFrame):
        """
        Add examples to self.examples

        Parameters
        ----------
        examples : pd.DataFrame
            New examples to add
        """
        self.examples = pd.concat([self.examples, examples])

    @configured_validate_arguments
    def head(self, n: int):
        """
        Returns a pd.DataFrame containing n first examples

        Parameters
        ----------
        n : int
            Number of examples to return

        Returns
        -------
        pd.DataFrame
            New examples
        """
        return self.examples.head(n)

    def to_html(self):
        """
        Renders html content to display examples

        Returns
        -------
        str
            HTML content
        """
        return self.examples.to_html()


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
        scan_examples: Optional[ScanExamples] = None,
        display_footer_info: bool = True,
        detector_name: str = None,
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
        level : Optional[IssueLevel]
            Level or severity of the issue, by default IssueLevel.MINOR.
        description : Optional[str]
            Description of the issue in human language.
        meta : Optional[dict]
            Additional metadata about the issue.
        transformation_fn : Optional[TransformationFunction]
            Transformation function, used for vulnerabilities detected via metamorphic testing, for example with
            perturbations of the inputs.
        slicing_fn : Optional[SlicingFunction]
            Slicing function, used for vulnerabilities affecting a single data slice.
        importance : Optional[float]
            Arbitrary importance score of the issue, used for ordering.
        examples : Optional[pd.DataFrame]
            Examples of the vulnerability as a `pandas.DataFrame`.
        features : Optional[List[str]]
            List of features affected by the issue.
        tests : Optional[Union[dict, callable]]
            Either a dictionary of tests, keyed by name, or a callable that returns a dictionary of tests. Each test is
            a test function from the giskard library (or a custom test defined by the ``@test`` decorator).
            For example, ``{"Test that accuracy is good": giskard.testing.tests.test_accuracy()}``.
        taxonomy : Optional[str]
            List of taxonomy machine tags, in MISP format. A machine tag is composed of a namespace (MUST), a predicate
            (MUST) and an (OPTIONAL) value, like ``namespace:predicate:value``.
        scan_examples : Optional[ScanExamples]
            A ScanExamples object to manage examples
        display_footer_info : Optional[bool]
            Whether to display warnings or not
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
        self._features = features
        self._tests = tests
        self.taxonomy = taxonomy or []
        self.display_footer_info = display_footer_info
        self.scan_examples = DataFrameScanExamples() if scan_examples is None else scan_examples
        if examples is not None:
            self.scan_examples.extend(examples)
        self._detector_name = detector_name

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

    @property
    def detector_name(self):
        return self._detector_name

    def set_detector_name(self, detector_name):
        self._detector_name = detector_name

    def examples(self, n=3) -> Any:
        return self.scan_examples.head(n)

    def add_examples(self, examples: Any):
        self.scan_examples.extend(examples)

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

To learn more about causes and solutions, check our [guide on robustness issues](https://docs.giskard.ai/en/stable/knowledge/key_vulnerabilities/robustness/index.html).
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

To learn more about causes and solutions, check our [guide on performance bias.](https://docs.giskard.ai/en/stable/knowledge/key_vulnerabilities/performance_bias/index.html)
""",
)

Overconfidence = IssueGroup(
    name="Overconfidence",
    description="""
We found some data slices in your dataset containing significant number of overconfident predictions. Overconfident predictions are rows that are incorrect but are predicted with high probabilities or confidence scores. This happens when:

- There are not enough examples in the overconfident data slice in the training set
- Wrongly labeled examples in the training set in the overconfident data slice
- For imbalanced datasets, the model may assign high probabilities to predictions of the majority class

To learn more about causes and solutions, check our [guide on overconfidence issues.](https://docs.giskard.ai/en/stable/knowledge/key_vulnerabilities/overconfidence/index.html)
""",
)

Underconfidence = IssueGroup(
    name="Underconfidence",
    description="""
We found some data slices in your dataset containing significant number of underconfident predictions. Underconfident predictions refer to situations where the predicted label has a probability that is very close to the probability of the next highest probability label. This happens when:

- There are not enough examples in the training set for the underconfident data slice
- The model is too simple and struggles to capture the complexity of the underlying data
- The underconfident data slice contains inherent noise or overlapping feature distributions

To learn more about causes and solutions, check our [guide on underconfidence issues.](https://docs.giskard.ai/en/stable/knowledge/key_vulnerabilities/underconfidence/index.html)
""",
)

Ethical = IssueGroup(
    name="Ethical",
    description="""
Your model seems to be sensitive to gender, ethnic, or religion based perturbations in the input data. These perturbations can include switching some words from feminine to masculine, countries or nationalities. This happens when:

- Underrepresentation of certain demographic groups in the training data
- Data is reflecting some structural biases and societal prejudices
- Use of complex models with large number of parameters that tend to overfit the training data

To learn more about causes and solutions, check our [guide on unethical behaviour.](https://docs.giskard.ai/en/stable/knowledge/key_vulnerabilities/ethics/index.html)""",
)

DataLeakage = IssueGroup(
    name="Data Leakage",
    description="""
Your model seems to present some data leakage. The model provides different results depending on whether it is computing on a single data point or the entire dataset. This happens when:

- Preprocessing steps, such as scaling, missing value imputation, or outlier handling, are fitted inside the prediction pipeline
- Train-test splitting is done after preprocessing or feature selection

To learn more about causes and solutions, check our [guide on data leakage.](https://docs.giskard.ai/en/stable/knowledge/key_vulnerabilities/data_leakage/index.html)""",
)

Stochasticity = IssueGroup(
    name="Stochasticity",
    description="""
Your model seems to present some stochastic behaviour. The model provides different results at each execution. This may happen when some stochastic training process is included in the prediction pipeline.

To learn more about causes and solutions, check our [guide on stochasticity issues.](https://docs.giskard.ai/en/stable/knowledge/key_vulnerabilities/stochasticity/index.html)""",
)

SpuriousCorrelation = IssueGroup(
    name="Spurious Correlation",
    description="""
We found some potential spurious correlations between your data and the model predictions. Some data slices are highly correlated with your predictions. This happens when:

- Data leakage: one of the feature is indirectly linked with the target variable
- Overfitting: the model learns specific noisy patterns of the training data, including coincidental correlations that are not causal
- Data noise: the training set contains anomalies that are unrelated to the underlying problem (data collection, measurement biases, data preprocessing issues, etc.)

To learn more about causes and solutions, check our [guide on spurious correlation.](https://docs.giskard.ai/en/stable/knowledge/key_vulnerabilities/spurious/index.html)""",
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
