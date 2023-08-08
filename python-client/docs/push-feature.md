# Push Feature Details

Up-to-date docs (Description, requirements,triggering event, text description) for each push feature

## Overconfidence

Title| Description
-- | --
Description| Tag **examples** that are incorrect but that were classified with a high probability as the wrong label
Requirement| Need ground truth, work on multi-label classification classified with a high probability as the wrong label, ONLY classification
Triggering event | When we switch examples, the example is incorrect and the probability difference between the predicted label probability and the ground truth probability is above 0.5. ( 1 / (3e-1 * (n - 2) + 2 - 1e-3 * (n - 2) ** 2) for multi-label classification, n=3 -> 0.44, n=4 -> 0.39, n=5 -> 0.36, etc)
Test description |  Check if this specific example is overconfident - one-sample test  (also created: "has the right label" and "probability of the right label probability increase")

```
"push_title": f"This example is incorrect while having a high confidence."
```

```
"action": "Save this example for further inspection and testing",
"explanation": "This may help you identify spurious correlation and create one-sample tests based on these examples",
"button": "Save Example"

"action": "Generate a one-sample test automatically to check if this example is correctly predicted",
"explanation": "This enables you to make sure this specific example is correct for a new model",
"button": "Create one-sample test"

"action": "Open the debugger session on similar examples",
"explanation": "Debugging similar examples may help you find common patterns",
"button": "Open debugger"
```

## Underconfidence

Title| Description
-- | --
Description| Tag **examples** that are classified with inconsistency
Requirement| ONLY classification, 
Triggering event | When we switch examples and the probability of the top label and the probability of the second top label have less than 10% difference for multi-label classification (predicted label probability - threshold for binary classification)
Test description |   Check if this specific example is underconfident - one-sample test  (also created: has the right label and probability of the right label probability increase)


```
"push_title":f"This example was predicted with very low confidence"
```

```
"action": "Save this example for further inspection and testing",
"explanation": "This may help you identify inconsistent patterns and create one-sample tests based on these examples",
"button": "Save Example"

"action": "Generate a one-sample test automatically the underconfidence"
"explanation": "This may help you ensure this example is not predicted with low confidence for a new model",
"button": "Create one-sample test"

"action": "Open the debugger session on similar examples",
"explanation": "Debugging similar examples may help you find common patterns",
"button": "Open debugger"
```

## Contribution Right Prediction

Title| Description
-- | --
Description|  Tag slices that contributes a lot to the prediction
Requirement| NA
Triggering event | When we switch examples and the most contributing shapley’s value is really high compared to the rest (clustering of the top 5 shapley values and return true is the biggest value is a cluster on itself)
Test description | Create Theil's U test automatically

```
"push_title": f"{str(feature)}=={str(value)} contributes a lot to the prediction",
```

```
"action": "Save slice and continue debugging session",
"explanation": "Saving the slice will enable you to create tests more efficiently",
"button": "Save Slice"

"action": "Generate a test to check if this correlation holds with the whole dataset",
"explanation": "Correlations may be spurious, double check if it has a business sense",
"button": "Create Test"

"action": "Open the debugger session on similar examples",
"explanation": "Debugging similar examples may help you find common patterns",
"button": "Open debugger"



```

## Contribution Wrong Prediction

Title| Description
-- | --
Description| Tag features that contribute a lot to the prediction when the example is incorrect
Requirement| Need ground truth
Triggering event | When we switch examples, the most contributing shapley’s value are high compared to the rest and the example is incorrect (clustering of the top 5 shapley values and return true is the biggest value is a cluster on itself)
Test description | Check if the performance of an F1-score/RMSE test is more than 10% different between a slice for the corresponding feature value and the whole dataset
```
"push_title": f"{str(feature)}=={str(value)} is responsible for the incorrect prediction",
```

```
"action": "Save slice and continue debugging session",
"explanation": "Saving the slice will enable you to create tests more efficiently",
"button": "Save Slice"

"action": "Generate a test to check if this correlation holds with the whole dataset",
"explanation": "Correlations may be spurious, double check if it has a business sense",
"button": "Create Test"

"action": "Open the debugger session on similar examples",
"explanation": "Debugging similar examples may help you find common spurious patterns",
"button": "Open Debugger"
```

## Perturbation 

Title| Description
-- | --
Description| Tag features that make the prediction change after a small variation
Requirement| Applicable only to numerical features and textual feature
Triggering event |  When we switch examples and the prediction changes after: 2 MAD (Median absolute deviation) variation or for textual feature, a small variation such as uppercase or punctuation transformation
Test description | Check if the prediction change ratio is not higher than a certain threshold after the perturbation of the whole dataset
```
 Check if the prediction change ratio is not higher than a certain threshold after the perturbation of the whole dataset
```

```
"action": "Generate a robustness test that slightly perturb this feature",
"explanation": "This will enable you to make sure the model is robust against similar small changes",
"button": "Create test"
```
