import contextlib
from typing import Optional, Tuple

try:
    import wandb  # noqa
    from wandb.wandb_run import Run
except ImportError as e:
    raise ImportError("The 'wandb' python package is not installed. To get it, run 'pip install wandb'.") from e


@contextlib.contextmanager
def wandb_run(project: Optional[str] = None, **kwargs) -> Run:
    wandb.run = wandb.run or wandb.init(project=project or "giskard", **kwargs)
    wandb.run._label(repo="Giskard")  # noqa
    yield wandb.run


def _parse_test_name(test_name: str) -> Tuple[str, str]:
    """[Temporary] Get a metric and a data slice from a test name."""
    test_name = test_name.split("on data slice")
    metric_name, data_slice = test_name[0], test_name[-1]
    data_slice = data_slice.replace('"', "")
    return metric_name, data_slice
