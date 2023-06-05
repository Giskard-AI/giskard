# Credit scoring (sklearn model)

## Libraries import
```python
import pandas as pd
import pytest
from sklearn import model_selection
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn import model_selection
from giskard import Model, Dataset
```

## Wrapping dataset
```python
column_types = {
    "account_check_status": "category",
    "duration_in_month": "numeric",
    "credit_history": "category",
    "purpose": "category",
    "credit_amount": "numeric",
    "savings": "category",
    "present_emp_since": "category",
    "installment_as_income_perc": "numeric",
    "sex": "category",
    "personal_status": "category",
    "other_debtors": "category",
    "present_res_since": "numeric",
    "property": "category",
    "age": "numeric",
    "other_installment_plans": "category",
    "housing": "category",
    "credits_this_bank": "numeric",
    "job": "category",
    "people_under_maintenance": "numeric",
    "telephone": "category",
    "foreign_worker": "category",
}

df = pd.read_csv(
    "https://raw.githubusercontent.com/Giskard-AI/giskard-examples/main\
    /datasets/credit_scoring_classification_model_dataset/german_credit_prepared.csv",
    keep_default_na=False,
    na_values=["_GSK_NA_"],
)
```
```python
wrapped_dataset = Dataset(df,
                               name='Test german credit scoring dataset',
                               target="default",
                               column_types=column_types)
```
## Wrapping model
```python
    columns_to_scale = [key for key in column_types.keys() if column_types[key] == "numeric"]

numeric_transformer = Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())])

columns_to_encode = [key for key in column_types.keys() if column_types[key] == "category"]

categorical_transformer = Pipeline(
    [
        ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse=False)),
    ]
)

preprocessor = ColumnTransformer(
    transformers=[
        ("num", numeric_transformer, columns_to_scale),
        ("cat", categorical_transformer, columns_to_encode),
    ]
)
clf = Pipeline(steps=[("preprocessor", preprocessor), ("classifier", LogisticRegression(max_iter=100))])

Y = german_credit_data.df["default"]
X = german_credit_data.df.drop(columns="default")
X_train, X_test, Y_train, Y_test = model_selection.train_test_split(
    X, Y, test_size=0.20, random_state=30, stratify=Y  # NOSONAR
)
clf.fit(X_train, Y_train)
```
```python
wrapped_model = Model(model=clf,
                           model_type="classification",
                           feature_names=list(column_types.keys()))
```