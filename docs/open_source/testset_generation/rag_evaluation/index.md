# 🥇 RAGET Evaluation

After automatically generating a test set for your RAG agent using RAGET, you can then evaluate the **correctness
of the agent's answers** compared to the reference answers (using a LLM-as-a-judge approach). The main purpose
of this evaluation is to help you **identify the weakest components in your RAG agent**.

> ℹ️ You can find a [tutorial](../../../reference/notebooks/RAGET_IPCC.ipynb) where we demonstrate the capabilities of RAGET
> with a simple RAG agent build with LlamaIndex
> on the IPCC report.

## Correctness Evaluation on the Generated Test Set

First, you need to wrap your RAG agent in a function that takes a question as input and returns an answer. For
conversational agents, we will also pass a `history` parameter which will contain a list of dictionaries in OpenAI chat
format (e.g. `{"role": "user", "content": "What is the capital of France?"}`).

Then, you can evaluate your RAG agent using the `giskard.rag.evaluate` function. This function will compare the answers
of your RAG agent with the reference answers in the test set.

```python
from giskard.rag import evaluate

# Wrap your RAG model
def get_answer_fn(question: str, history=None) -> str:
    """A function representing your RAG agent."""
    # Format appropriately the history for your RAG agent
    messages = history if history else []
    messages.append({"role": "user", "content": question})

    # Get the answer
    answer = get_answer_from_agent(messages)  # could be langchain, llama_index, etc.

    return answer


# Run the evaluation and get a report
report = evaluate(get_answer_fn, testset=testset, knowledge_base=knowledge_base)
```

The evaluation generates a {class}`~giskard.rag.RAGReport` object. Once you get your report, you can display it in a
notebook or save it as an HTML file.

```python
display(report)  # if you are working in a notebook

# or save the report as an HTML file
report.to_html("rag_eval_report.html")
```

This report is what you'll obtain:
![image](../../../_static/raget.png)

### RAG Components Scores

RAGET computes scores for each component of the RAG agent. The scores are computed by aggregating the correctness
of the agent's answers on different question types (see question type to component mapping [here](q_types)).
Each score grades a component on a scale from 0 to 100, 100 being a perfect score. **Low scores can help you identify
weaknesses of your RAG agent and which components need improvement.**

Here is the list of components evaluated with RAGET:

- **`Generator`**: the LLM used inside the RAG to generate the answers
- **`Retriever`**: fetch relevant documents from the knowledge base according to a user query
- **`Rewriter`** (optional): rewrite the user query to make it more relevant to the knowledge base or to account for chat history
- **`Router`** (optional): filter the query of the user based on his intentions (intentions detection)
- **`Knowledge Base`**: the set of documents given to the RAG to generate the answers

### Analyze Correctness and Failures

You can access the correctness of the agent aggregated in various ways or analyze only it failures:

```python
# Correctness on each topic of the Knowledge Base
report.correctness_by_topic()

# Correctness on each type of question
report.correctness_by_question_type()

# get all the failed questions
report.failures

# get the failed questions filtered by topic and question type
report.get_failures(topic="Topic from your knowledge base", question_type="simple")
```

You can also export the report to a pandas DataFrame to analyze the results programmatically:

```python
results = report.to_pandas()
```

### RAGAS Metrics

**You can pass additional evaluation metrics to the `evaluate` function**. They will be computed during the evaluation.
We currently provide [RAGAS metrics](https://docs.ragas.io/en/latest/concepts/metrics/index.html) as additional metrics.

The results of your metrics will be displayed in the report object as histograms and will be available inside the report main `DataFrame`.
![image](../../../_static/ragas_metrics.png)

To include RAGAS metrics in evaluation, make sure to have installed the `ragas>=0.1.5` library. Some of the RAGAS metrics need access to the contexts retrieved by the RAG agent for each question. These can be returned by the `get_answer_fn` function along with the answer to the question:

```python
from giskard.rag import AgentAnswer

def get_answer_fn(question: str, history=None) -> str:
    """A function representing your RAG agent."""
    # Format appropriately the history for your RAG agent
    messages = history if history else []
    messages.append({"role": "user", "content": question})

    # Get the answer and the documents
    agent_output = get_answer_from_agent(messages)

    # Following llama_index syntax, you can get the answer and the retrieved documents
    answer = agent_output.text
    documents = agent_output.source_nodes

    # Instead of returning a simple string, we return the AgentAnswer object which
    # allows us to specify the retrieved context which is used by RAGAS metrics
    return AgentAnswer(
        message=answer,
        documents=documents
    )
```

Then, you can include the RAGAS metrics in the evaluation:

```python
from giskard.rag.metrics.ragas_metrics import ragas_context_recall, ragas_faithfulness

report = evaluate(
    get_answer_fn,
    testset=testset,
    knowledge_base=knowledge_base,
    metrics=[ragas_context_recall, ragas_faithfulness]
)
```

Built-in metrics include `ragas_context_precision`, `ragas_faithfulness`, `ragas_answer_relevancy`,
`ragas_context_recall`. Note that including these metrics can significantly increase the evaluation time and LLM usage.

Alternatively, you can directly pass a list of answers instead of `get_answer_fn` to the `evaluate` function, you can then pass the retrieved documents as an optional argument `retrieved_documents` to compute the RAGAS metrics.

### Creating Custom Metrics

**You can easily create your own metrics by extending the base Metric class from Giskard.** 

To illustrate how simple it is to build a custom metric, we’ll implement the `CorrectnessScoreMetric` — a custom metric that evaluates the performance of a language model as a judge. 

While `Giskard` provides a default boolean correctness metric to check if a RAG (Retrieval-Augmented Generation) answer is correct, in this case, we want to generate a numerical score to gain deeper insights into the model's performance.

#### Step 1: Building the Prompts

Before we can evaluate the model's output, we need to craft a system prompt and input template for the language model. The system prompt will instruct the LLM on how to evaluate the Q&A system’s response, and the input template will format the conversation history, agent’s response, and reference answer.

##### System Prompt

The system prompt provides the LLM with clear instructions on how to rate the agent's response. You’ll be guiding the LLM to give a score between 1 and 5 based on the correctness, accuracy, and factuality of the answer.

```python
SYSTEM_PROMPT = """Your task is to evaluate a Q/A system. 
The user will give you a question, an expected answer and the system's response.
You will evaluate the system's response and provide a score.
We are asking ourselves if the response is correct, accurate and factual, based on the reference answer.

Guidelines:
1. Write a score that is an integer between 1 and 5. You should refer to the scores description.
2. Follow the JSON format provided below for your output.

Scores description:
    Score 1: The response is completely incorrect, inaccurate, and/or not factual.
    Score 2: The response is mostly incorrect, inaccurate, and/or not factual.
    Score 3: The response is somewhat correct, accurate, and/or factual.
    Score 4: The response is mostly correct, accurate, and factual.
    Score 5: The response is completely correct, accurate, and factual.

Output Format (JSON only):
{{
    "correctness_score": (your rating, as a number between 1 and 5)
}}

Do not include any additional text—only the JSON object. Any extra content will result in a grade of 0.
"""
```

##### Input Template

The input template formats the actual content you will send to the model. This includes the conversation history, the agent's response, and the reference answer.

```python
INPUT_TEMPLATE = """
### CONVERSATION
{conversation}

### AGENT ANSWER
{answer}

### REFERENCE ANSWER
{reference_answer}
"""
```

#### Step 2: Subclassing the Metric Class

We implement the custom metric by subclassing the `Metric` class provided by `Giskard`.

```python
from giskard.rag.metrics.base import Metric

class CorrectnessScoreMetric(Metric):
    """
    Custom metric to evaluate the correctness of a system's response based on a reference answer.
    The metric returns a score between 1 and 5, with 1 being completely incorrect and 5 being completely correct.
    """

    def __call__(self, question_sample: dict, answer: AgentAnswer) -> dict:
        pass
```

Now all we need to do is to fill in this `__call__` method with our logic.

Metrics are meant to be used with the `evaluate` function. That is where we assume the inputs are coming from. 

Note the input types: 
- The `question_sample` is a dictionary that must have the following keys: `conversation_history`, `question` and `reference_answer`
- The `AgentAnswer` is a dataclass containing the output of the RAG system being evaluated. It is defined as follows:

```python
@dataclass
class AgentAnswer:
    message: str
    documents: Optional[Sequence[str]] = None
```

The core of our new metric consists in a litellm call with the prompts specified earlier. 

```python
from giskard.rag.question_generators.utils import parse_json_output
from giskard.rag.metrics.correctness import format_conversation
from giskard.llm.client import get_default_client

def __call__(self, question_sample: dict, answer: AgentAnswer) -> dict:

    # Retrieve the llm client
    llm_client = self._llm_client or get_default_client()

    # Call the llm
    out = llm_client.complete(
        messages=[
            ChatMessage(
                role="system",
                content=SYSTEM_PROMPT,
            ),
            ChatMessage(
                role="user",
                content=INPUT_TEMPLATE.format(
                    conversation=format_conversation(
                        question_sample.conversation_history
                        + [{"role": "user", "content": question_sample.question}]
                    ),
                    answer=answer.message,
                    reference_answer=question_sample.reference_answer,
                ),
            ),
        ],
        temperature=0,
        format="json_object",
    )

    # Parse the output string representation of a JSON object into a dictionary
    json_output = parse_json_output(
        out.content,
        llm_client=llm_client,
        keys=["correctness_score"],
        caller_id=self.__class__.__name__,
    )

    return json_output
```

Note how the `keys=["correctness_score"]` must match with the keys you asked from the llm in your `SYSTEM_PROMPT`.

As you can see, it is as simple as calling our llm and parsing its output as a dictionary with one key, `correctness_score`, containing the score given by the LLM. 

<details>
  <summary>Putting everything together, here is our final implementation:</summary>

```python
from giskard.llm.client import get_default_client
from giskard.llm.errors import LLMGenerationError

from giskard.rag.metrics.base import Metric
from giskard.rag.question_generators.utils import parse_json_output
from giskard.rag.metrics.correctness import format_conversation

SYSTEM_PROMPT = """Your task is to evaluate a Q/A system. 
The user will give you a question, an expected answer and the system's response.
You will evaluate the system's response and provide a score.
We are asking ourselves if the response is correct, accurate and factual, based on the reference answer.

Guidelines:
1. Write a score that is an integer between 1 and 5. You should refer to the scores description.
2. Follow the JSON format provided below for your output.

Scores description:
    Score 1: The response is completely incorrect, inaccurate, and/or not factual.
    Score 2: The response is mostly incorrect, inaccurate, and/or not factual.
    Score 3: The response is somewhat correct, accurate, and/or factual.
    Score 4: The response is mostly correct, accurate, and factual.
    Score 5: The response is completely correct, accurate, and factual.

Output Format (JSON only):
{{
    "correctness_score": (your rating, as a number between 1 and 5)
}}

Do not include any additional text—only the JSON object. Any extra content will result in a grade of 0.
"""

INPUT_TEMPLATE = """
### CONVERSATION
{conversation}

### AGENT ANSWER
{answer}

### REFERENCE ANSWER
{reference_answer}
"""

class CorrectnessScoreMetric(Metric):
    """
    Custom metric to evaluate the correctness of a system's response based on a reference answer.
    The metric returns a score between 1 and 5, with 1 being completely incorrect and 5 being completely correct.
    """

    def __call__(self, question_sample: dict, answer: AgentAnswer) -> dict:
        """
        Compute the correctness *as a number from 1 to 5* between the agent answer and the reference answer.

        Parameters
        ----------
        question_sample : dict
            A question sample from a QATestset.
        answer : AgentAnswer
            The answer of the agent on the question.

        Returns
        -------
        dict
            The result of the correctness scoring. It contains the key 'correctness_score'.
            
        Raises
        ------
        LLMGenerationError
            If there is an issue during the LLM evaluation process.
        """

        # Implement your LLM call with litellm
        llm_client = self._llm_client or get_default_client()
        try:
            out = llm_client.complete(
                messages=[
                    ChatMessage(
                        role="system",
                        content=SYSTEM_PROMPT,
                    ),
                    ChatMessage(
                        role="user",
                        content=INPUT_TEMPLATE.format(
                            conversation=format_conversation(
                                question_sample.conversation_history
                                + [{"role": "user", "content": question_sample.question}]
                            ),
                            answer=answer.message,
                            reference_answer=question_sample.reference_answer,
                        ),
                    ),
                ],
                temperature=0,
                format="json_object",
            )
            
            # We asked the LLM to output a JSON object, so we must parse the output into a dict
            json_output = parse_json_output(
                out.content,
                llm_client=llm_client,
                keys=["correctness_score"],
                caller_id=self.__class__.__name__,
            )

            return json_output

        except Exception as err:
            raise LLMGenerationError("Error while evaluating the agent") from err
```
</details> 

#### Step 3: Use Your New Metric in the Evaluation Function

Integrating our new custom metric into the evaluation process is straightforward. Simply instantiate the metric and pass it to the `evaluate` function.

```python
# Instantiate the custom correctness metric
correctness_score = CorrectnessScoreMetric(name="correctness_score")

# Run the evaluation with the custom metric
report = evaluate(
    answer_fn,
    testset=testset, # a QATestset instance
    knowledge_base=knowledge_base, # the knowledge base used for building the QATestset 
    metrics=[correctness_score]
)
``` 

Again, be careful that the `name` argument in the `CorrectnessScoreMetric` match the key you return in the output dictionary.

#### Wrap-up

In this tutorial, we covered the steps to create and use a custom evaluation metric. 

Here's a quick summary of the key points:
1. *Define the prompts*: Create a system prompt and input template for the LLM to evaluate answers.
2. *Implement the new metric*: Subclass the `Metric` class and implement the `__call__` method to create the custom `CorrectnessScoreMetric`.
3. *Use the new metric*: Instantiate and integrate the custom metric into the evaluation function.

## Troubleshooting

If you encounter any issues, join our [Discord community](https://discord.gg/fkv7CAr3FE) and ask questions in our #support channel.
