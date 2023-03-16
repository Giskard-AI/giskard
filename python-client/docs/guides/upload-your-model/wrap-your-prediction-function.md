---
description: How to wrap a prediction function with all the preprocessing steps in Giskard?
---

# Wrap your prediction function

To inspect & test your model, we ask you to upload a `prediction_function` that **contains** **all the preprocessing steps** (feature engineering, scaling, missing value imputation, etc.).

\
The **easiest way is to use an ML Pipeline** as your `predict_proba` function (see the [example below](wrap-your-prediction-function.md#wrap-a-prediction-function-without-a-pipeline-1)). If you don't have such a pipeline, no problem! We provide you with an example without a pipeline!

{% hint style="info" %}
**The two reasons why we ask you to turn your model into a pipeline**

* We have a **holistic approach** to ML inspection & test: an ML model is not only the ML inference step. It's the whole pipeline that creates the results. Many bugs and strange behaviors are coming from the pre-processing steps
* We want to detect errors that require **domain knowledge**: we use human-readable datasets to inspect & test ML models
{% endhint %}

### Wrap manually a prediction function <mark style="background-color:orange;">without</mark> a pipeline

Here is an [example](https://colab.research.google.com/drive/1K6L9IOryfphNzK4hPi1BX1Qv7GC2o3uk#scrollTo=JW9crRujO7H\_) that illustrates how to upload a `prediction_function` that wraps multiple feature\_engineering steps for the Iris data:

* Add / remove variables
* Scaling of a numeric variable
* One hot encoding of a categorical variable

```python
def wrapped_prediction_function(X):
  #Create a new numerical variable that computes the Sepal area
  X["sepal area"] = X["sepal length (cm)"] * X["sepal width (cm)"]
  
  #Turn sepal width (cm) into a categorical variable
  bins = [-np.inf, 2.5, 3.5, np.inf]
  labels = ["small","medium","big"]
  X["cat_sepal_width"] = pd.cut(X["sepal width (cm)"], bins=bins, labels=labels)

  #Scale all the numerical variables
  num_cols = ["sepal area", "petal length (cm)", "petal width (cm)"]
  X[num_cols] = std_slc.transform(X[num_cols])

  #Use OneHotEncoder with cat_sepal_width
  arr =  one_hot_encoder.transform(X[['cat_sepal_width']]).toarray()
  X = X.join(pd.DataFrame(arr))

  #Remove Sepal length, sepal width and cat_sepal_width
  X = X.drop(columns= ["sepal width (cm)", "sepal length (cm)", "cat_sepal_width"])

  return knn.predict_proba(X)
```

Then you can easily upload your `wrapped_prediction_function` using the following code

```python
iris.upload_model_and_df(
    prediction_function=wrapped_prediction_function, 
    model_type='classification',
    df=df_iris, #the dataset you want to use to inspect your model
    column_types={"sepal length (cm)":"numeric", "sepal width (cm)": "numeric", "petal length (cm)": "numeric", "petal width (cm)": "numeric", "target":"category"}, #all the column types of df
    target='target', #the column name in df corresponding to the actual target variable (ground truth).
    feature_names=["sepal length (cm)","sepal width (cm)", "petal length (cm)", "petal width (cm)"],
    classification_labels=knn.classes_
)
```

To execute the whole **notebook** for the above example, use the following notebook in Colab:

{% embed url="https://colab.research.google.com/drive/1K6L9IOryfphNzK4hPi1BX1Qv7GC2o3uk#scrollTo=JW9crRujO7H_" %}

### Use pipeline to automatically wrap your prediction function

The proper and easiest way to upload a model in Giskard is to provide a model **pipeline** to the upload function in Giskard.&#x20;

{% hint style="info" %}
To put your model to production, it's a common practice to turn all your data preprocessing, training, and inference steps into one unique pipeline. For example, see [here](https://scikit-learn.org/stable/modules/generated/sklearn.pipeline.Pipeline.html) how to do this with sklearn.
{% endhint %}

Here is an [example](https://github.com/Giskard-AI/giskard/blob/main/giskard-demo-notebook/notebook/Email%20Classification%20Model.ipynb) of a sklearn pipeline that computes feature engineering steps for numeric, category, and text variables at the same time!

```python
feature_types = {i:column_types[i] for i in column_types if i!='Target'}

columns_to_scale = [key for key in feature_types.keys() if feature_types[key]=="numeric"]

numeric_transformer = Pipeline([('imputer', SimpleImputer(strategy='median')),
    ('scaler', StandardScaler())])


columns_to_encode = [key for key in feature_types.keys() if feature_types[key]=="category"]

categorical_transformer = Pipeline([
        ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
        ('onehot', OneHotEncoder(handle_unknown='ignore',sparse=False)) ])
text_transformer = Pipeline([
                      ('vect', CountVectorizer(stop_words=stoplist)),
                      ('tfidf', TfidfTransformer())
                     ])
preprocessor = ColumnTransformer(
    transformers=[
      ('num', numeric_transformer, columns_to_scale),
      ('cat', categorical_transformer, columns_to_encode),
      ('text_Mail', text_transformer, "Content")
    ]
)
clf = Pipeline(steps=[('preprocessor', preprocessor),
                      ('classifier', LogisticRegression(max_iter =1000))])
```

Then to upload to Giskard, you just need to call the `predict_proba` method of the pipeline class:

```python
enron.upload_model_and_df(
    prediction_function=clf.predict_proba, 
    model_type='classification',
    df=test_data, #the dataset you want to use to inspect your model
    column_types=column_types, #all the column types of df
    target='Target', #the column name in df corresponding to the actual target variable (ground truth).
    feature_names=list(feature_types.keys()),#list of the feature names of prediction_function
    classification_labels=clf.classes_
)
```

To execute the whole **notebook** for the above example, use the following [notebook](https://github.com/Giskard-AI/giskard/blob/main/giskard-demo-notebook/notebook/Email%20Classification%20Model.ipynb):

{% embed url="https://github.com/Giskard-AI/giskard/blob/main/giskard-demo-notebook/notebook/Email%20Classification%20Model.ipynb" %}
