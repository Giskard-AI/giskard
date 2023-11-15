import pytest

from giskard.ml_worker import websocket
from giskard.ml_worker.exceptions.IllegalArgumentError import IllegalArgumentError
from giskard.ml_worker.websocket.listener import (
    function_argument_to_ws,
    parse_function_arguments,
)

TEST_PROJECT_KEY = "123"
TEST_MODEL_ID = "231"
TEST_DATASET_ID = "321"
TEST_FUNC_ARGUMENT_FLOAT = 114.514
TEST_FUNC_ARGUMENT_INT = 114
TEST_FUNC_ARGUMENT_STR = "giskard"
TEST_FUNC_ARGUMENT_BOOL = False


def test_function_argument_to_ws():
    # Domain classes creation should be tested somewhere else, do not test them.
    #   "dataset": Dataset,
    #   "model": BaseModel,
    #   "slicingFunction": SlicingFunction,
    #   "transformFunction": TransformationFunction,
    kwargs = {
        "float": TEST_FUNC_ARGUMENT_FLOAT,
        "int": TEST_FUNC_ARGUMENT_INT,
        "str": TEST_FUNC_ARGUMENT_STR,
        "bool": TEST_FUNC_ARGUMENT_BOOL,
        "list": [1, 2, 3],  # List should be a kwargs
        "dict": {"key": "value"},
    }
    args = function_argument_to_ws(kwargs)
    assert len(args) == len(kwargs.values()) - 1
    assert args[0].float_arg == TEST_FUNC_ARGUMENT_FLOAT
    assert args[1].int_arg == TEST_FUNC_ARGUMENT_INT
    assert args[2].str_arg == TEST_FUNC_ARGUMENT_STR
    assert args[3].bool_arg == TEST_FUNC_ARGUMENT_BOOL  # Processed as an integer, filed in GSK-1557
    assert args[4].kwargs == str("kwargs['list'] = [1, 2, 3]\nkwargs['dict'] = {'key': 'value'}")


def test_parse_function_arguments():
    with pytest.raises(IllegalArgumentError):
        parse_function_arguments(None, [websocket.FuncArgument(name="invalid", none=False)])

    # Domain classes need client to download, do not test them here.
    #   "dataset": Dataset,
    #   "model": BaseModel,
    #   "slicingFunction": SlicingFunction,
    #   "transformFunction": TransformationFunction,
    args = [
        websocket.FuncArgument(name="none", none=True),
        websocket.FuncArgument(name="float", none=False, float=TEST_FUNC_ARGUMENT_FLOAT),
        websocket.FuncArgument(name="int", none=False, int=TEST_FUNC_ARGUMENT_INT),
        websocket.FuncArgument(name="str", none=False, str=TEST_FUNC_ARGUMENT_STR),
        websocket.FuncArgument(name="bool", none=False, bool=TEST_FUNC_ARGUMENT_BOOL),
        websocket.FuncArgument(name="kwargs", none=False, kwargs=f"kwargs['bool1'] ={TEST_FUNC_ARGUMENT_BOOL}"),
    ]
    kwargs = parse_function_arguments(None, args)
    assert "none" not in kwargs.keys()  # None should not be here
    assert "float" in kwargs.keys() and kwargs["float"] == TEST_FUNC_ARGUMENT_FLOAT
    assert "int" in kwargs.keys() and kwargs["int"] == TEST_FUNC_ARGUMENT_INT
    assert "str" in kwargs.keys() and kwargs["str"] == TEST_FUNC_ARGUMENT_STR
    assert "bool" in kwargs.keys() and kwargs["bool"] == TEST_FUNC_ARGUMENT_BOOL
    assert "kwargs" in kwargs.keys() and kwargs["kwargs"]["bool1"] == TEST_FUNC_ARGUMENT_BOOL
