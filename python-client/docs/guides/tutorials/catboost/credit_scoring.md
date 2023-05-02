# Credit scoring (catboost model)

## Libraries import

```python
import pandas as pd
from catboost import CatBoostClassifier
from sklearn import model_selection
from giskard import wrap_model, Dataset
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
columns_to_encode = [key for key in column_types.keys() if column_types[key] == "category"]

Y = df["default"]
X = df.drop(columns="default")
X_train, X_test, Y_train, Y_test = model_selection.train_test_split(
    X, Y, test_size=0.20, random_state=30, stratify=Y
)
cb = CatBoostClassifier(iterations=2, learning_rate=1, depth=2)
cb.fit(X_train, Y_train, columns_to_encode)
```
```python
wrapped_model = wrap_model(model=cb,
                           model_type="classification",
                           feature_names=list(column_types.keys()))
```