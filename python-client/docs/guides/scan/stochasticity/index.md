## Report

<aside>
⛔ Your model provides different results at each execution. For example, a first execution of prediction_model(data.iloc[[4]]) provides 0.09 while a second execution provides 0.008.

</aside>

## Explanation

<aside>
👨‍🦰 If your training process is included inside your model, you may have different results at each execution. Data leakage refers to the situation where information from outside the training data set is unintentionally used to create a model. This can happen when your preprocessing steps, such as scaling or missing value imputation or outlier handling, is fitted inside your prediction pipeline.

</aside>

## Action

<aside>
👉 We strongly recommend you **remove all training process in your prediction model. We recommend you to fix a random seed.**

</aside>
