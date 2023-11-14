import random
import re
import string

import numpy as np
import pandas as pd
from scipy.stats import median_abs_deviation

from giskard.ml_worker.testing.registry.transformation_function import transformation_function

from ....llm import get_default_client

nearbykeys = {
    "a": ["q", "w", "s", "x", "z"],
    "b": ["v", "g", "h", "n"],
    "c": ["x", "d", "f", "v"],
    "d": ["s", "e", "r", "f", "c", "x"],
    "e": ["w", "s", "d", "r"],
    "f": ["d", "r", "t", "g", "v", "c"],
    "g": ["f", "t", "y", "h", "b", "v"],
    "h": ["g", "y", "u", "j", "n", "b"],
    "i": ["u", "j", "k", "o"],
    "j": ["h", "u", "i", "k", "n", "m"],
    "k": ["j", "i", "o", "l", "m"],
    "l": ["k", "o", "p"],
    "m": ["n", "j", "k", "l"],
    "n": ["b", "h", "j", "m"],
    "o": ["i", "k", "l", "p"],
    "p": ["o", "l"],
    "q": ["w", "a", "s"],
    "r": ["e", "d", "f", "t"],
    "s": ["w", "e", "d", "x", "z", "a"],
    "t": ["r", "f", "g", "y"],
    "u": ["y", "h", "j", "i"],
    "v": ["c", "f", "g", "v", "b"],
    "w": ["q", "a", "s", "e"],
    "x": ["z", "s", "d", "c"],
    "y": ["t", "g", "h", "u"],
    "z": ["a", "s", "x"],
}

gruber = re.compile(
    r"""(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))"""
)  # noqa


@transformation_function(name="Keyboard typo", tags=["text"], cell_level=True)
def keyboard_typo_transformation(text: str, rate: float = 0.1) -> str:
    """
    Generate a random typo from words of the text of 'column_name'
    Typos are generated through character substitution based on keyboard proximity
    """
    # Split the text into words
    if pd.isnull(text):
        return text

    words = text.split(" ")

    # Introduce typos into some of the words
    for i in range(len(words)):
        if random.random() < rate:
            word = words[i]
            if len(word) > 1:
                j = random.randint(0, len(word) - 1)
                c = word[j]
                if c in nearbykeys:
                    replacement = random.choice(nearbykeys[c])
                    words[i] = word[:j] + replacement + word[j + 1 :]

    # Join the words back into a string
    return " ".join(words)


@transformation_function(name="To uppercase", tags=["text"], cell_level=True)
def uppercase_transformation(text: str) -> str:
    """
    Transform the text to uppercase
    """
    return np.nan if pd.isnull(text) else text.upper()


@transformation_function(name="To lowercase", tags=["text"], cell_level=True)
def lowercase_transformation(text: str) -> str:
    """
    Transform the text of the column 'column_name' to lowercase
    """
    return np.nan if pd.isnull(text) else text.lower()


@transformation_function(name="Strip punctuation", tags=["text"], cell_level=True)
def strip_punctuation(text: str) -> str:
    """
    Remove all punctuation symbols (e.g., ., !, ?) from the text of the column 'column_name'
    """
    if pd.isnull(text):
        return text

    split_urls_from_text = gruber.split(text)

    # The non-URLs are always even-numbered entries in the list and the URLs are odd-numbered.
    for i in range(0, len(split_urls_from_text), 2):
        split_urls_from_text[i] = split_urls_from_text[i].translate(str.maketrans("", "", string.punctuation))

    stripped_text = "".join(split_urls_from_text)

    return stripped_text


@transformation_function(name="Change writing style", row_level=False, tags=["text"])
def change_writing_style(df: pd.DataFrame, column_name: str, style: str) -> pd.DataFrame:
    sys_prompt = f"""Your task is to rewrite user-provided text using a given style.

Your goal is to rewrite the provided text according to the specified style. Do not add extra sentences in your answer, only include the rewritten text:
Please ensure that your rewritten text retains the meaning of the original text as much as possible, keep the same
language.

Here is an example:
SYSTEM: Your writing style is: informal
USER: The Third Council of Constantinople, counted as the Sixth Ecumenical Council by the Eastern Orthodox and Catholic Churches, as well as by certain other Western Churches, met in 680–681 and condemned monoenergism and monothelitism as heretical and defined Jesus Christ as having two energies and two wills (divine and human).
ASSISTANT: So, there was this big meeting called the Third Council of Constantinople, which some churches refer to as the Sixth Ecumenical Council. It happened in 680–681, and they basically said that monoenergism and monothelitism were heretical. They also made it clear that Jesus Christ has two energies and two wills, one divine and one human.

Now it’s your turn. Your writing style is: {style}
"""

    client = get_default_client()

    def _rewrite(text):
        llm_output = client.complete(
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": text},
            ],
            model="gpt-3.5-turbo",
            caller_id="change_writing_style_transormation",
        )
        return llm_output.message

    new_df = df.copy()
    new_df[column_name] = df[column_name].apply(_rewrite)

    return new_df


def compute_mad(x):
    return median_abs_deviation(x, scale=1)


@transformation_function(name="MAD Increment", tags=["num"], row_level=False)
def mad_transformation(
    data: pd.DataFrame, column_name: str, factor: float = 1, value_added: float = None
) -> pd.DataFrame:
    """
    Add 3 times the value_added to the column, or if unavailable, add 3 times the MAD value.
    """
    data = data.copy()
    if value_added is None:
        value_added = compute_mad(data[column_name])
    data[column_name] = data[column_name].apply(lambda x: x + factor * value_added)
    return data


@transformation_function(name="Add value", tags=["numerical"], row_level=False)
def add_value(data: pd.DataFrame, column_name: str, value_added: float = 0.0) -> pd.DataFrame:
    """
    Add the value_added to the column.
    """
    data = data.copy()
    data[column_name] = data[column_name].apply(lambda x: x + value_added)
    return data
