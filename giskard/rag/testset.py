from typing import TYPE_CHECKING, Any, Dict, Optional, Sequence

import json
import logging
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from datasets import Dataset as HFDataset
from datasets import load_dataset
from huggingface_hub import DatasetCard

if TYPE_CHECKING:
    from huggingface_hub import CommitInfo

from ..core.suite import Suite
from ..datasets.base import Dataset
from ..testing.tests.llm import test_llm_correctness

logger = logging.getLogger(__name__)


@dataclass
class QuestionSample:
    id: str
    question: str
    reference_answer: str
    reference_context: str
    conversation_history: Sequence[Dict[str, str]]
    metadata: Dict[str, Any]
    agent_answer: Optional[str] = None
    correctness: Optional[bool] = None

    def to_dict(self):
        sample_dict = {
            "id": self.id,
            "question": self.question,
            "reference_answer": self.reference_answer,
            "reference_context": self.reference_context,
            "conversation_history": self.conversation_history,
            "metadata": self.metadata,
        }
        if self.agent_answer is not None:
            sample_dict["agent_answer"] = self.agent_answer
        if self.correctness is not None:
            sample_dict["correctness"] = self.correctness
        return sample_dict


class QATestset:
    """A class to represent a testset for QA models."""

    def __init__(self, question: Sequence[QuestionSample]):
        self._questions = question
        self._dataframe = pd.DataFrame.from_records([question.to_dict() for question in self._questions]).set_index(
            "id"
        )

    def __len__(self):
        return len(self._dataframe)

    @classmethod
    def from_pandas(cls, dataframe: pd.DataFrame):
        return cls([QuestionSample(**record) for record in dataframe.to_dict(orient="records")])

    def to_pandas(self, filters: Optional[dict] = None):
        """Return the testset as a pandas DataFrame.

        Parameters
        ----------
        filters : dict, optional
            A dictionary of filters to apply to the testset. The keys are the metadata names and the values are list of kept values.
            If multiple metadata are provided, the filters are combined with an AND operator.

        """

        if filters is not None:
            return self._dataframe[
                self._dataframe["metadata"].apply(lambda x: all(x.get(k) in v for k, v in filters.items()))
            ]
        return self._dataframe

    def to_dataset(self, filters: Optional[dict] = None):
        dataframe = self.to_pandas(filters=filters).copy()
        dataframe["conversation_history"] = dataframe["conversation_history"].apply(lambda x: json.dumps(x))
        dataframe["metadata"] = dataframe["metadata"].apply(lambda x: json.dumps(x))
        return Dataset(dataframe, name="QA Testset", target=False, validation=False)

    def get_metadata_values(self, metadata_name: str):
        """Return the unique values of a metadata field."""
        metadata_values = list(
            set([metadata[metadata_name] for metadata in self._dataframe["metadata"] if metadata_name in metadata])
        )
        metadata_values.sort()
        return metadata_values

    def count_sample_by_metadata(self, metadata_name: str):
        """Count the number of samples for each value of a metadata field."""
        return self._dataframe["metadata"].apply(lambda x: x.get(metadata_name)).value_counts()

    def save(self, path):
        """Save the testset as a JSONL file.

        Parameters
        ----------
        path : str
            The path to the output JSONL file.
        """
        self._dataframe.reset_index().to_json(path, orient="records", lines=True, force_ascii=False)

    @classmethod
    def load(cls, path):
        """Load a testset from a JSONL file.

        Parameters
        ----------
        path : str
            The path to the input JSONL file.
        """
        dataframe = pd.read_json(path, orient="records", lines=True)
        return cls.from_pandas(dataframe)

    def push_to_hf_hub(
        self,
        repo_id: str,
        token: str = None,
        private: bool = False,
        **kwargs: Any,
    ) -> "CommitInfo":
        """Push the QATestset to the Hugging Face Hub.

        Parameters
        ----------
        repo_id : str
            The repository ID on the Hugging Face Hub.
        token : str, optional
            Authentication token for private repositories. Defaults to None.
        private : bool
            Whether to create a private repository. Defaults to False.
        **kwargs : Any
            Additional arguments passed to Dataset.push_to_hub().

        Returns
        -------
        CommitInfo
            The commit information.
        """

        # Conversion to Dataset from the datasets library
        dataset = HFDataset.from_pandas(self._dataframe)
        dataset.push_to_hub(repo_id, token=token, private=private, **kwargs)

        # Load the dataset card template
        template_path = Path(__file__).parent / "dataset_card_template.md"
        template = template_path.read_text()

        # Make and push the dataset card
        try:
            from ..llm.client import get_default_client

            config = {"metadata": get_default_client().get_config()}
        except Exception:
            config = {}
        content = template.format(repo_id=repo_id, num_items=len(self._dataframe), config=json.dumps(config, indent=4))
        return DatasetCard(content=content).push_to_hub(repo_id=repo_id, token=token, repo_type="dataset")

    @classmethod
    def load_from_hf_hub(cls, repo_id: str, token: str = None, **kwargs: Any) -> "QATestset":
        """
        Load an instance of the class from the Hugging Face Hub.

        Parameters
        ----------
        repo_id : str
            The repository ID on the Hugging Face Hub.
        token : str, optional
            Authentication token for private repositories. Defaults to None.
        **kwargs : Any
            Additional arguments passed to `load_dataset`.

        Returns
        -------
        QATestset
            An instance of the class itself loaded from the Hub.

        Raises
        ------
        ImportError
            If required dependencies are not installed.
        """
        dataset = load_dataset(repo_id, token=token, split="train", **kwargs)
        dataframe = pd.DataFrame(dataset)
        return cls.from_pandas(dataframe)

    def to_test_suite(self, name=None, slicing_metadata: Optional[Sequence[str]] = None):
        """
        Convert the testset to a Giskard test suite.

        Parameters
        ----------
        name : str, optional
            The name of the test suite. If not provided, the name will be "Test suite generated from testset".

        Returns
        -------
        giskard.Suite
            The test suite.
        """

        if slicing_metadata is None:
            suite_default_params = {"dataset": self.to_dataset()}
            name = name or "Test suite generated from testset"
            suite = Suite(name=name, default_params=suite_default_params)
            suite.add_test(test_llm_correctness, "TestsetCorrectnessTest", "TestsetCorrectnessTest")
        else:
            name = name or "Test suite generated from testset"
            suite = Suite(name=name)
            for metadata_name in slicing_metadata:
                metadata_values = self.get_metadata_values(metadata_name)
                for value in metadata_values:
                    suite.add_test(
                        test_llm_correctness(dataset=self.to_dataset(filters={metadata_name: [value]})),
                        f"TestsetCorrectnessTest_{metadata_name}_{value}",
                        f"TestsetCorrectnessTest_{metadata_name}_{value}",
                    )
        return suite

    def copy(self):
        """Return a copy of the testset."""
        return QATestset(self._dataframe.copy())

    @property
    def samples(self):
        return self._questions
