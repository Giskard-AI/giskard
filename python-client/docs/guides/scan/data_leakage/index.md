## Report

<aside>
⛔ Your model may have some data leakage. For example, your model provides different results depending on whether it’s computing on a single data or whole data. For example, the following examples provides different result:

</aside>

`prediction_model(data)[34] is not equal with prediction_model(data.iloc[[34]])`

## Explanation

<aside>
👨‍🦰 Data leakage refers to the situation where information from outside the training data set is unintentionally used to create a model. This can happen when your preprocessing steps, such as scaling or missing value imputation or outlier handling, is fitted inside your prediction pipeline.

</aside>

## Action

<aside>
👉 To avoid this issue we strongly recommend you separate your training steps and inference steps using different pipelines.

</aside>
