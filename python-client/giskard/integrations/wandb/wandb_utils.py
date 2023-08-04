import contextlib
from typing import Optional

try:
    import wandb  # noqa
    from wandb.wandb_run import Run
except ImportError as e:
    raise ImportError("The 'wandb' python package is not installed. " "To get it, run 'pip install wandb'.") from e


@contextlib.contextmanager
def wandb_run(project: Optional[str] = None, **kwargs) -> Run:
    wandb.run = wandb.run or wandb.init(project=project or "giskard", **kwargs)
    wandb.run._label(repo="Giskard")  # noqa
    yield wandb.run
