from pathlib import Path

# We import lightgbm as the first thing here to avoid a bug on macOS that happens when lgbm is imported after torch.
# See https://github.com/dmlc/xgboost/issues/7039#issuecomment-860910066
import lightgbm  # noqa: F401
import torch  # noqa: F401


def path(p):
    return Path(__file__).parent / p
