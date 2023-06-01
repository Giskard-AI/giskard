# Unrobustness

The unrobustness issue in machine learning refers to the phenomenon where a model's predictions are highly sensitive to small perturbations in the input data. These perturbations can include adding typos, changing word order, or turning text into uppercase or lowercase. Despite the seemingly insignificant nature of these perturbations, they can significantly impact the model's predictions, leading to erroneous or inconsistent results.

## Causes of Unrobustness Against Small Text Perturbations

Several factors can contribute to the occurrence of unrobustness in machine learning models against small text perturbations:

1. **Lack of Robust Feature Representation**: If the model's input representation does not capture the underlying semantics and meaning of the text effectively, small perturbations can cause substantial changes in the feature space. As a result, the model may not be able to generalize well and make consistent predictions, leading to unrobust behavior.

2. **Overreliance on Shallow Linguistic Patterns**: Some models may rely heavily on shallow linguistic patterns, such as specific word
3. **Overfitting**: When your model learned noise (out of distribution), its results may vary against small changes

## Action

We strongly recommend you **inspect** the volatile examples. This will enable you to find

- The right data augmentation strategy to make your model invariant to small changes
- The right feature engineering techniques to reduce the complexity of your model
- The regularization techniques to avoid overfitting

