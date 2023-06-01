import os
import re
import logging
import string
import random
import warnings
from typing import Union, List
from dataclasses import dataclass

import nltk
import torch
import numpy as np
import pandas as pd
from nltk.corpus import stopwords
from torch.utils.data import DataLoader
from torch.utils.data import TensorDataset
from sklearn.metrics import classification_report
from transformers import AutoModel, AutoModelForSequenceClassification, AutoTokenizer

import giskard
from giskard import Dataset, Model

logger = logging.getLogger(__name__)
nltk.download('stopwords')

# Constants
STOP_WORDS = set(stopwords.words('english'))

PRETRAINED_WEIGHTS_NAME = "distilbert-base-uncased"

TEXT_COLUMN_NAME = "Review"
TARGET_COLUMN_NAME = "label"

RANDOM_SEED = 0
