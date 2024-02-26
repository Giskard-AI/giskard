from enum import Enum


class QuestionTypes(int, Enum):
    EASY = 1
    COMPLEX = 2
    DISTRACTING_ELEMENT = 3
    SITUATIONAL = 4
    DOUBLE_QUESTION = 5
    CONVERSATIONAL = 6
    MULTI_CONTEXT = 7
    OUT_OF_SCOPE = 8
