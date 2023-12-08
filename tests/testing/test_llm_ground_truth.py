import numpy as np
import pandas as pd
import pytest
from langchain.chains import LLMChain
from langchain.llms.fake import FakeListLLM

from giskard import Model, Dataset
from giskard.testing.tests.llm import test_llm_ground_truth_similarity, test_llm_ground_truth

INPUT_DATA = [
    "Hello",
    "Hi, how are you?",
    "I translate in French",
    "Hey there!",
    "What's up?",
    "Can you help me with something?",
    "Good morning!",
    "How's your day going?",
    "I need assistance with a task.",
    "Greetings!",
    "Tell me about yourself.",
]

CLASSIFICATION_TARGET = [
    "GREETING",
    "GREETING",
    "SENTENCE",
    "GREETING",
    "GREETING",
    "REQUEST",
    "GREETING",
    "GREETING",
    "REQUEST",
    "GREETING",
    "REQUEST",
]

TRANSLATION_TARGET = [
    "Bonjour",
    "Salut, comment ca va",
    "Je traduis en français",
    "Salut!",
    "Quoi de neuf?",
    "Pouvez-vous m'aider avec quelque chose?",
    "Bonjour!",
    "Comment se passe votre journée?",
    "J'ai besoin d'aide pour une tâche.",
    "Salutations!",
    "Parlez-moi de vous.",
]

SIMILAR_TRANSLATION_TARGET = [
    "Salut",
    "Salut, ça va bien?",
    "Je traduis dans la langue de Molière",
    "Hey!",
    "Du nouveau?",
    "Peux-tu me donner un coup de main?",
    "Hello!",
    "Comment ça va aujourd'hui?",
    "Peux-tu m'aider avec ça?",
    "Salut à tous!",
    "Dis-moi un peu plus sur toi.",
]

CLASSIFICATION_DATASET = Dataset(
    pd.DataFrame(
        {
            "text": INPUT_DATA,
            "target": CLASSIFICATION_TARGET,
        }
    ),
    target="target",
)

TRANSLATION_DATASET = Dataset(
    pd.DataFrame(
        {
            "text": INPUT_DATA,
            "target": TRANSLATION_TARGET,
        }
    ),
    target="target",
)


@pytest.mark.memory_expensive
@pytest.mark.parametrize(
    "test,dataset,responses,should_pass, failed_mask",
    [
        (
            test_llm_ground_truth,
            CLASSIFICATION_DATASET,
            CLASSIFICATION_TARGET,
            True,
            [False] * len(CLASSIFICATION_TARGET),
        ),
        (
            test_llm_ground_truth,
            CLASSIFICATION_DATASET,
            ["GREETING"] * len(CLASSIFICATION_TARGET),
            True,
            np.array(CLASSIFICATION_TARGET) != "GREETING",
        ),
        (
            test_llm_ground_truth,
            CLASSIFICATION_DATASET,
            ["REQUEST"] * len(CLASSIFICATION_TARGET),
            False,
            np.array(CLASSIFICATION_TARGET) != "REQUEST",
        ),
        (
            test_llm_ground_truth_similarity,
            TRANSLATION_DATASET,
            TRANSLATION_TARGET,
            True,
            [False] * len(CLASSIFICATION_TARGET),
        ),
        (
            test_llm_ground_truth_similarity,
            TRANSLATION_DATASET,
            SIMILAR_TRANSLATION_TARGET,
            True,
            [False] * len(CLASSIFICATION_TARGET),
        ),
        (
            test_llm_ground_truth_similarity,
            TRANSLATION_DATASET,
            ["L'imagination est plus importante que le savoir."] * len(TRANSLATION_TARGET),
            False,
            [True] * len(CLASSIFICATION_TARGET),
        ),
    ],
)
def test_of_test_llm_ground_truth(test, dataset, responses, should_pass, failed_mask):
    model = _make_model(responses)

    result = test(model, dataset).execute()

    assert result.passed is should_pass
    expected_output_df = dataset.df[failed_mask]
    assert list(expected_output_df.index) == list(result.output_ds[0].df.index)


def _make_model(responses):
    llm = FakeListLLM(responses=responses)
    chain = LLMChain.from_string(llm=llm, template="This is a sample prompt: {text}")
    model = Model(
        chain,
        "text_generation",
        feature_names=["text"],
        name="This is a sample model",
        description="This model is doing a sample task",
    )
    return model


@pytest.mark.parametrize(
    "test",
    [test_llm_ground_truth, test_llm_ground_truth_similarity],
)
def test_ground_truth_exact_no_target(test):
    model = _make_model(CLASSIFICATION_TARGET)

    dataset = Dataset(
        pd.DataFrame(
            {
                "text": INPUT_DATA,
            }
        )
    )

    with pytest.raises(ValueError):
        test(model, dataset).execute()
