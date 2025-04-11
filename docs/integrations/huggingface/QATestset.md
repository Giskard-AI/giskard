# 📤 Push a QATestset to the Hugging Face Hub

**Learn how to upload and manage your QATestset on the Hugging Face Hub using the `push_to_hf_hub` feature.**

This tutorial will guide you through the steps to push a dataset to the Hugging Face Hub and load it back for reuse.

## Install Required Dependencies

Before you begin, ensure you have the necessary libraries installed. Run the following command to install the `datasets` and `huggingface_hub` packages:

```bash
pip install datasets huggingface_hub
```

## Authenticate with Hugging Face

Set your Hugging Face authentication token (`HF_TOKEN`) to enable access to your account. You can generate your token from your [Hugging Face account settings](https://huggingface.co/settings/tokens).

## Push Your Dataset to the Hub

Use the `push_to_hf_hub` method to upload your dataset to the Hugging Face Hub. Replace `<username>` with your Hugging Face username and `<dataset_name>` with the desired name for your dataset:

This example demonstrates how to load a `QATestset` from the file `test_set.jsonl` and push it to the Hugging Face Hub:

```python
from giskard.rag.testset import QATestset
test_set = QATestset.load("test_set.jsonl")
test_set.push_to_hf_hub("<username>/<dataset_name>")
```

Once the dataset is successfully pushed, it will be available on your Hugging Face profile.

## Load the Dataset from the Hub

To reuse the dataset, you can load it back using the `load_from_hf_hub` method. This example demonstrates how to load the dataset and convert it to a pandas DataFrame for inspection:

```python
from giskard.rag.testset import QATestset
dset = QATestset.load_from_hf_hub("<username>/<dataset_name>")
dset.to_pandas().head()
```

Replace `<username>` and `<dataset_name>` with the appropriate values.

## Benefits of Using the Hugging Face Hub

By leveraging this integration, you can:

- Seamlessly share datasets across projects and collaborators.
- Reuse datasets without the need for manual file transfers.
- Access datasets directly from the Hugging Face Hub for streamlined workflows.

Start pushing your datasets today and take advantage of the collaborative power of the Hugging Face Hub!