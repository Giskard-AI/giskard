from enum import Enum


class QuestionTypes(int, Enum):
    EASY = 1
    COMPLEX = 2
    DISTRACTING_ELEMENT = 3
    SITUATIONAL = 4
    DOUBLE_QUESTION = 5
    CONVERSATIONAL = 6
    REASONING = 7
    MULTI_CONTEXT = 8
    OUT_OF_SCOPE = 9
