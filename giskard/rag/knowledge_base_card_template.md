---
tags:
- giskard
- knowledge-base
- information-retrieval

task_categories:
- text-generation
- text2text-generation
- question-answering
- text-retrieval
---

# Dataset Card for {repo_id}
> This repository was created using the [giskard](https://github.com/Giskard-AI/giskard) library, an open-source Python framework designed to evaluate and test AI systems. 

This dataset comprises a giskard's `KnowledgeBase` containing {num_items} documents. If embeddings were generated before the saving process, they are included and will be automatically loaded into a vector store when required.

## Usage

You can load this knowledge base using the following code:

```python
from giskard.rag import KnowledgeBase
kb = KnowledgeBase.load_from_hf_hub("{repo_id}")
```

## Configuration

The configuration details for this Knowledge Base (can also be found in the `config.json` file):

```bash
{config}
```

---

<h2 style="text-align: center;">
  <span style="display: inline-flex; align-items: center;">
    Built with 
    <a href="https://giskard.ai" target="_blank" style="display: inline-flex;">
      <img src="https://cdn.prod.website-files.com/601d6f7d0b9c984f07bf10bc/62983fa8ef716259c397a57d_logo.svg" 
             alt="Giskard Logo" 
             width="100">
    </a>
  </span>
</h2>

<div style="text-align: center;">
  <a href="https://github.com/Giskard-AI/giskard" target="_blank" style="display: inline-flex;"> Giskard </a> helps identify performance, bias, and security issues in AI applications, supporting both LLM-based systems like RAG agents and traditional machine learning models for tabular data.
</div>