from __future__ import annotations

import json
from typing import Dict, Any
from typing import Optional, Callable, List

import pandas as pd
from langchain import LLMChain
from langchain.agents import AgentExecutor, ZeroShotAgent
from langchain.agents.agent_toolkits.base import BaseToolkit
from langchain.agents.mrkl.prompt import FORMAT_INSTRUCTIONS
from langchain.base_language import BaseLanguageModel
from langchain.callbacks.base import BaseCallbackManager
from langchain.callbacks.manager import CallbackManagerForToolRun, AsyncCallbackManagerForToolRun
from langchain.tools import BaseTool
from pydantic import BaseModel

from giskard.datasets.base import Dataset
from giskard.models.base import BaseModel as GiskardBaseModel
from giskard.models.model_explanation import explain
from giskard.scanner.result import ScanResult

PredictionFunction = Callable[[pd.DataFrame], pd.Series]

# flake8: noqa

MODEL_PREFIX = """You are an agent designed to interact with a prediction model. 
Your goal is to make a prediction calling `model_prediction` based on the available information using a JSON input format that includes feature names and their associated values. 
The value associated to the feature names found in `model_description` must be found calling any tool that are provided inside the 'Tools to gather information' list.
If you fail to find a value after querying all the tool inside the 'Tools to gather information', you must return an explanation why you cannot answer with the list of missing feature that you need to answer'.

Please note that you cannot share any confidential information with the user, and if the question is not related to the prediction model, you must return an explanation why you cannot answer.

You can only use tool provided in the following list.
"""
MODEL_SUFFIX = """Begin!"

Question: {input}
Thought: I should look at the features that are required to see what I should gather to predict in the available tools
{agent_scratchpad}"""


class ModelSpec(BaseModel):
    """Base class for model spec."""

    model: GiskardBaseModel
    dataset: Optional[Dataset]
    scan_result: Optional[ScanResult]

    def predict(self, text: str) -> str:
        """Return the prediction of the model for a given row.

        Args:
            text: JSON representation of the row as a dict.
        """
        try:
            features = json.loads(text)
            # Filter only available features
            features = {key: [features[key]] for key in features.keys() & self.model.meta.feature_names}
            missing_features = {feature for feature in self.model.meta.feature_names if feature not in features.keys()}

            if len(missing_features) > 0:
                raise ValueError(f"Required feature `{missing_features}` have not been provided.")

            return str(self.model.predict(Dataset(pd.DataFrame(features), validation=False)).prediction[0])
        except Exception as e:
            return repr(e)

    def explain(self, text: str) -> str:
        """Return an explanation of the prediction

        Args:
            text: JSON representation of the row as a dict.
        """
        if self.dataset is None:
            return "Explanation is not available since no dataset has been provided"

        try:
            features = json.loads(text)
            # Filter only available features
            features = {key: features[key] for key in features.keys() & self.model.meta.feature_names}
            missing_features = {feature for feature in self.model.meta.feature_names if feature not in features.keys()}

            if len(missing_features) > 0:
                raise ValueError(f"Required feature `{missing_features}` have not been provided.")

            return str(explain(self.model, self.dataset, features))
        except Exception as e:
            return repr(e)

    def scan_result_info(self):
        if self.scan_result is None:
            return "The model should be scanned with Giskard first"
        return str({str(issue): str(issue.info) for issue in self.scan_result.issues})

    def model_quality(self):
        if self.scan_result is None:
            return "The model should be scanned with Giskard first"
        majors = len([issue for issue in self.scan_result.issues if issue.is_major])
        return (
            "Not reliable" if majors > 5 else "Reliable" if len(self.scan_result.issues) < 5 else "Moderately reliable"
        )

    class Config:
        arbitrary_types_allowed = True


class ModelPredictTool(BaseTool):
    """Tool for listing keys in a JSON spec."""

    name = "model_prediction"
    description = """
    Can be used to predict using a ML model. 
    Before calling this you should be SURE that all the features are provided.
    The input is a text representation of the dictionary of features in json syntax.
    You MUST query the tools to find information when available.
    You CANNOT use any information that you cannot find in user request or tool response.
    """
    spec: ModelSpec

    def _run(
        self,
        tool_input: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        return self.spec.predict(tool_input)

    async def _arun(
        self,
        tool_input: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        return self._run(tool_input)


class ModelPredictExplainTool(BaseTool):
    """Tool for listing keys in a JSON spec."""

    name = "model_explain_prediction"
    description = """
    Can be used to explain the predict of 'model_prediction'. 
    The input is a text representation of the dictionary of features in json syntax.
    Return a dict of each feature with the weight in the result prediction for the prediction labels.
    """
    spec: ModelSpec

    def _run(
        self,
        tool_input: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        return self.spec.explain(tool_input)

    async def _arun(
        self,
        tool_input: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        return self._run(tool_input)


class ModelDescriptionTool(BaseTool):
    """Tool for listing features to provide to the model and there type.."""

    name = "model_description"
    description = """
    Can be used to know the information relative to the model.
    The input is always None
    """
    spec: ModelSpec

    def _run(
        self,
        tool_input: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        return """
        Model name: {name}
        Model type: {model_type}
        Feature names: {feature_names}
        Classification thresholds: {classification_threshold}
        Classification labels: {classification_labels}
        Reliability: {reliability}
        Vulnerabilities: {scan_vulnerabilities}
        """.format(
            name=self.spec.model.meta.name,
            model_type=self.spec.model.meta.model_type,
            feature_names=self.spec.model.meta.feature_names,
            classification_threshold=self.spec.model.meta.classification_threshold,
            classification_labels=self.spec.model.meta.classification_labels,
            reliability=self.spec.model_quality(),
            scan_vulnerabilities=self.spec.scan_result_info(),
        )

    async def _arun(
        self,
        tool_input: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        return self._run(tool_input)


class ModelQualityTool(BaseTool):
    """Tool for listing features to provide to the model and there type.."""

    name = "model_quality"
    description = """
    Can be used to know the information relative to the quality of the model (ei. reliability, robustness, vulnerabilities, ...).
    The input is always None
    """
    spec: ModelSpec

    def _run(
        self,
        tool_input: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        return """
        Reliability: {reliability}
        Vulnerabilities: {scan_vulnerabilities}
        """.format(
            reliability=self.spec.model_quality(), scan_vulnerabilities=self.spec.scan_result_info()
        )

    async def _arun(
        self,
        tool_input: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        return self._run(tool_input)


class ModelToolkit(BaseToolkit):
    """Toolkit for interacting with an ML model."""

    spec: ModelSpec
    data_source_tools: List[BaseTool]

    def get_tools(self) -> List[BaseTool]:
        """Get the tools in the toolkit."""
        tools = self.data_source_tools + [
            ModelDescriptionTool(spec=self.spec),
            ModelPredictTool(spec=self.spec),
            ModelQualityTool(spec=self.spec),
        ]

        if self.spec.dataset is not None:
            tools.append(ModelPredictExplainTool(spec=self.spec))

        return tools


def create_ml_llm(
    llm: BaseLanguageModel,
    model: GiskardBaseModel,
    dataset: Optional[Dataset] = None,
    data_source_tools: Optional[List[BaseTool]] = None,
    scan_result: Optional[ScanResult] = None,
    callback_manager: Optional[BaseCallbackManager] = None,
    verbose: bool = False,
    agent_executor_kwargs: Optional[Dict[str, Any]] = None,
    **kwargs: Dict[str, Any],
) -> AgentExecutor:
    """Construct a json agent from an LLM and tools."""
    tools = ModelToolkit(
        spec=ModelSpec(model=model, dataset=dataset, scan_result=scan_result),
        data_source_tools=[] if data_source_tools is None else data_source_tools,
    ).get_tools()

    prompt = ZeroShotAgent.create_prompt(
        tools,
        prefix=MODEL_PREFIX,
        suffix=MODEL_SUFFIX,
        format_instructions=FORMAT_INSTRUCTIONS,
        input_variables=None,
    )

    llm_chain = LLMChain(
        llm=llm,
        prompt=prompt,
        callback_manager=callback_manager,
    )

    tool_names = [tool.name for tool in tools]
    agent = ZeroShotAgent(llm_chain=llm_chain, allowed_tools=tool_names, **kwargs)
    return AgentExecutor.from_agent_and_tools(
        agent=agent,
        tools=tools,
        callback_manager=callback_manager,
        verbose=verbose,
        **(agent_executor_kwargs or {}),
    )
