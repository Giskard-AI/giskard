from typing import Any, Callable, Dict, Iterable, Optional, Tuple, Union

from pathlib import Path

import pandas as pd

from giskard.core.core import SupportedModelTypes
from giskard.core.validation import configured_validate_arguments
from giskard.models.base import WrapperModel


class LangchainModel(WrapperModel):
    @configured_validate_arguments
    def __init__(
        self,
        model,
        model_type: SupportedModelTypes,
        name: Optional[str] = None,
        description: Optional[str] = None,
        data_preprocessing_function: Optional[Callable[[pd.DataFrame], Any]] = None,
        model_postprocessing_function: Optional[Callable[[Any], Any]] = None,
        feature_names: Optional[Iterable] = None,
        classification_threshold: Optional[float] = 0.5,
        classification_labels: Optional[Iterable] = None,
        **kwargs,
    ) -> None:
        assert (
            model_type == SupportedModelTypes.TEXT_GENERATION
        ), "LangchainModel only support text_generation ModelType"

        from langchain import LLMChain

        super().__init__(
            model=model,
            model_type=model_type,
            name=name,
            description=str(model.prompt.dict())
            if description is None and isinstance(model, LLMChain)
            else description,
            data_preprocessing_function=data_preprocessing_function,
            model_postprocessing_function=model_postprocessing_function,
            feature_names=feature_names,
            classification_threshold=classification_threshold,
            classification_labels=classification_labels,
            **kwargs,
        )

    def save(self, local_path: Union[str, Path], *args, **kwargs) -> None:
        super().save(local_path, *args, **kwargs)
        self.save_model(local_path)
        self.save_artifacts(Path(local_path) / "artifacts")

    def save_model(self, local_path: Union[str, Path], *args, **kwargs) -> None:
        path = Path(local_path)
        self.model.save(path / "chain.json")

    def save_artifacts(self, artifact_dir, *args, **kwargs) -> None:
        ...

    @classmethod
    def load(cls, local_dir, model_py_ver: Optional[Tuple[str, str, str]] = None, *args, **kwargs):
        constructor_params = cls.load_constructor_params(local_dir, *args, **kwargs)

        artifacts = cls.load_artifacts(Path(local_dir) / "artifacts") or dict()
        constructor_params.update(artifacts)

        return cls(model=cls.load_model(local_dir, model_py_ver=model_py_ver, **artifacts), **constructor_params)

    @classmethod
    def load_model(cls, local_dir, model_py_ver: Optional[Tuple[str, str, str]] = None, *args, **kwargs):
        from langchain.chains import load_chain

        path = Path(local_dir)
        return load_chain(path / "chain.json", **kwargs)

    @classmethod
    def load_artifacts(cls, local_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        ...

    def model_predict(self, df):
        generations = [self.model(data) for data in df.to_dict("records")]
        output_keys = self.model.output_keys

        if len(output_keys) == 1:
            return [generation[output_keys[0]] for generation in generations]
        else:
            return [
                str({key: value for key, value in generation.items() if key in output_keys})
                for generation in generations
            ]
