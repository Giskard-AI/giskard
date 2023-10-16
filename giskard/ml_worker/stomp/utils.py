from typing import Tuple

import re
from re import Match

from giskard.ml_worker.stomp.constants import (
    CR,
    HEADER_TRANSFORMATIONS,
    LF,
    REGEX_DECODE,
    REGEX_ENCODE,
)


def read_line(frame: str) -> Tuple[str, str]:
    splitted = frame.split(LF, 1)
    if len(splitted) == 1:
        raise ValueError("Should have EOL")
    line, data = splitted
    if len(line) > 0 and line[-1] == CR:
        line = line[:-2]
    return line, data


def _encode_decode(encode: bool = True):
    def transformation(match: Match) -> str:
        keys = list(match.groupdict().keys)
        if len(keys) != 1:
            raise ValueError("Should not happen")
        key = keys[0]
        return HEADER_TRANSFORMATIONS[key][0 if encode else 1]

    return transformation


ENCODER = _encode_decode(True)
DECODER = _encode_decode(False)


def untransform_header_data(data: str) -> str:
    return re.sub(REGEX_DECODE, DECODER, data)


def transform_header_data(data: str) -> str:
    return re.sub(REGEX_ENCODE, ENCODER, data)


def validate_header_part(part: str) -> str:
    # TODO
    # Check for bad escape
    return part
