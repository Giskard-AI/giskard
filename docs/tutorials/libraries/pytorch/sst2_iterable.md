# SST-2 Binary text classification with XLM-ROBERTA

## Libraries import
```python
import pandas as pd
import torch
import torch.nn as nn
import torchtext.functional as F
import torchtext.transforms as T
from torch.hub import load_state_dict_from_url
from torchdata.datapipes.iter import IterableWrapper
from torchtext.datasets import SST2
from torchtext.models import RobertaClassificationHead, XLMR_BASE_ENCODER
from giskard import Model, Dataset
```

## Wrap dataset
```python
dev_datapipe = SST2(split="dev")
dev_dataframe = pd.DataFrame(dev_datapipe, columns=["text", "label"])
```
```python
wrapped_dataset = Dataset(dev_dataframe.head(), 
                               name="test dataset", 
                               target="label")
```

## Wrap model
```python
torch_softmax = nn.Softmax(dim=1)
device = "cuda" if torch.cuda.is_available() else "cpu"

padding_idx = 1
bos_idx = 0
eos_idx = 2
max_seq_len = 256
xlmr_vocab_path = r"https://download.pytorch.org/models/text/xlmr.vocab.pt"
xlmr_spm_model_path = r"https://download.pytorch.org/models/text/xlmr.sentencepiece.bpe.model"

text_transform = T.Sequential(
    T.SentencePieceTokenizer(xlmr_spm_model_path),
    T.VocabTransform(load_state_dict_from_url(xlmr_vocab_path)),
    T.Truncate(max_seq_len - 2),
    T.AddToken(token=bos_idx, begin=True),
    T.AddToken(token=eos_idx, begin=False),
)
batch_size = 1

num_classes = 2
input_dim = 768

classifier_head = RobertaClassificationHead(num_classes=num_classes, input_dim=input_dim)
model = XLMR_BASE_ENCODER.get_model(head=classifier_head, load_weights=False).to(device)


# Transform the raw dataset using non-batched API (i.e apply transformation line by line)
def apply_transform(x):
    return text_transform(x[0]), x[1]

def pandas_to_torch(test_df):
    test_datapipe_transformed = IterableWrapper(dev_dataframe.head()["text"]).map(apply_transform)
    data_list = []
    for entry in test_datapipe_transformed:
        data_list.append(F.to_tensor([entry[0]], padding_value=padding_idx).to(device))

    return data_list

classification_labels = [0, 1]

def my_softmax(x):
    return torch_softmax(x)
```
```python
wrapped_model = Model(name="SST2-XLMR_BASE_ENCODER",
                           model=model,
                           feature_names=["text"],
                           model_type="classification",
                           classification_labels=classification_labels,
                           data_preprocessing_function=pandas_to_torch,
                           model_postprocessing_function=my_softmax,
)
```
