from dataclasses import dataclass


@dataclass
class PredictFromDatasetTool:
    name: str = "predict_from_dataset"
    description: str = ("1) Extracts rows from the dataset using the filtering expression;"
                        "2) Returns model prediction for the extracted rows.")
    parameters: list = ()
    parameters_required: list = ()

    def __call__(self, *args, **kwargs) -> str:
        """Must return a tool in the next format:
        {
            "type": "function",
            "function": {
                "name": "get_current_weather",
                "description": "Get the current weather in a given location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA",
                        },
                        "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                    },
                    "required": ["location"],
                },
            },
        }
        """
        ...
