
Available Metric functions
==========================

Correctness
-----------
Using LLM as a judge strategy, the correctness metrics check if an answer is correct compared to the reference answer.

.. autofunction:: giskard.rag.metrics.correctness.correctness_metric

RAGAS Metrics
-------------
We provide wrappers for some RAGAS metrics. You can implement other RAGAS metrics using the `RAGASMetric` class. 
.. autofunction:: giskard.rag.metrics.ragas_metrics.ragas_context_precision

.. autofunction:: giskard.rag.metrics.ragas_metrics.ragas_faithfulness

.. autofunction:: giskard.rag.metrics.ragas_metrics.ragas_answer_relevancy

.. autofunction:: giskard.rag.metrics.ragas_metrics.ragas_context_recall

Base Metric
-----------
.. autoclass:: giskard.rag.metrics.Metric
    :members:
    :special-members: __call__


