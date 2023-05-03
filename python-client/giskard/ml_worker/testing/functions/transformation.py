import os
import random
import string

import pandas as pd

from giskard.ml_worker.testing.registry.transformation_function import transformation_function

nearbykeys = {
    'a': ['q', 'w', 's', 'x', 'z'],
    'b': ['v', 'g', 'h', 'n'],
    'c': ['x', 'd', 'f', 'v'],
    'd': ['s', 'e', 'r', 'f', 'c', 'x'],
    'e': ['w', 's', 'd', 'r'],
    'f': ['d', 'r', 't', 'g', 'v', 'c'],
    'g': ['f', 't', 'y', 'h', 'b', 'v'],
    'h': ['g', 'y', 'u', 'j', 'n', 'b'],
    'i': ['u', 'j', 'k', 'o'],
    'j': ['h', 'u', 'i', 'k', 'n', 'm'],
    'k': ['j', 'i', 'o', 'l', 'm'],
    'l': ['k', 'o', 'p'],
    'm': ['n', 'j', 'k', 'l'],
    'n': ['b', 'h', 'j', 'm'],
    'o': ['i', 'k', 'l', 'p'],
    'p': ['o', 'l'],
    'q': ['w', 'a', 's'],
    'r': ['e', 'd', 'f', 't'],
    's': ['w', 'e', 'd', 'x', 'z', 'a'],
    't': ['r', 'f', 'g', 'y'],
    'u': ['y', 'h', 'j', 'i'],
    'v': ['c', 'f', 'g', 'v', 'b'],
    'w': ['q', 'a', 's', 'e'],
    'x': ['z', 's', 'd', 'c'],
    'y': ['t', 'g', 'h', 'u'],
    'z': ['a', 's', 'x'],
}


@transformation_function(name="Keyboard typo", tags=['text'])
def keyboard_typo_transformation(x: pd.Series, column_name: str, rate: float = 0.1) -> pd.Series:
    """
    Generate a random typo from words of the text of 'column_name'
    Typos are generated through character substitution based on keyboard proximity
    """
    # Split the text into words
    words = x[column_name].split(" ")

    # Introduce typos into some of the words
    for i in range(len(words)):
        if random.random() < rate:
            word = words[i]
            if len(word) > 1:
                j = random.randint(0, len(word) - 1)
                c = word[j]
                if c in nearbykeys:
                    replacement = random.choice(nearbykeys[c])
                    words[i] = word[:j] + replacement + word[j + 1:]

    # Join the words back into a string
    x[column_name] = ' '.join(words)
    return x


@transformation_function(name="To uppercase", tags=['text'])
def uppercase_transformation(x: pd.Series, column_name: str) -> pd.Series:
    """
    Transform the text of the column 'column_name' to uppercase
    """
    x[column_name] = x[column_name].upper()
    return x


@transformation_function(name="To lowercase", tags=['text'])
def lowercase_transformation(x: pd.Series, column_name: str) -> pd.Series:
    """
    Transform the text of the column 'column_name' to lowercase
    """
    x[column_name] = x[column_name].lower()
    return x


@transformation_function(name="Strip punctuation", tags=['text'])
def strip_punctuation(x: pd.Series, column_name: str):
    """
    Remove all punctuation symbols (e.g., ., !, ?) from the text of the column 'column_name'
    """
    x[column_name] = x[column_name].translate(str.maketrans('', '', string.punctuation))
    return x


@transformation_function(name="Change writing style", row_level=False, tags=['text'])
def change_writing_style(x: pd.DataFrame, index: int, column_name: str, style: str,
                         OPENAI_API_KEY: str) -> pd.DataFrame:
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
    rewrite_prompt_template = """
    As a text rewriting robot, your task is to rewrite a given text using a specified rewriting style. You will receive a prompt with the following format:
    ```
    "TEXT"
    ===
    "REWRITING STYLE"
    ```
    Your goal is to rewrite the provided text according to the specified style. The purpose of this task is to evaluate how the rewritten text will affect our machine learning models.

    Your response should be in the following format:
    ```
    REWRITTEN TEXT
    ```
    Please ensure that your rewritten text is grammatically correct and retains the meaning of the original text as much as possible. Good luck!
    ```
    "TEXT": {text}
    ===
    "REWRITING STYLE": {style}
    ```
    """

    from langchain import PromptTemplate
    from langchain import LLMChain
    from langchain import OpenAI

    rewrite_prompt = PromptTemplate(input_variables=['text', 'style'], template=rewrite_prompt_template)
    chain_rewrite = LLMChain(llm=OpenAI(), prompt=rewrite_prompt)

    x.at[index, column_name] = chain_rewrite.run({'text': x.at[index, column_name], 'style': style})
    return x
