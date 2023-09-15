# Push Feature Details

Up-to-date docs (Description, requirements,triggering event, text description) for each push feature

## Overconfidence

Title| Description
-- | --
Description| Tag **examples** that are incorrect but that were classified with a high probability as the wrong label
Requirement| Need ground truth, work on multi-label classification classified with a high probability as the wrong label
Triggering event | When we switch examples, the example is incorrect and the probability of the predicted label is at least twice superior as the ground truth prediction probability
Test description |  Check if this specific example has the right label with enough confidence.

```
"push_title": f"This example is incorrect while having a high confidence."
```

```
# Disabled temporarily
#    "action": "Save this example for further inspection and testing",
#    "explanation": "This may help you identify spurious correlation and create unit test based on "
#    "these examples",
#    "button": "Save Example",

"action": "Generate a unit test to check if this example is correctly predicted",
"explanation": "This enables you to make sure this specific example is correct for a new model",
"button": "Create unit test"

"action": "Open the debugger session on similar examples",
"explanation": "Debugging similar examples may help you find common patterns",
"button": "Open debugger"
```

## Underconfidence

Title| Description
-- | --
Description| Tag examples that are classified with inconsistency
Requirement| Is not applicable to regression
Triggering event | When we switch examples and the probability of the top label and the probability of the second top label have less than 10% difference
Test description |  Check if this specific example has the right label with enough confidence.

```
"push_title":f"This example was predicted with very low confidence"
```

```
# Disabled Temporarily
# "action": "Save this example for further inspection and testing",
# "explanation": "This may help you identify inconsistent patterns and create a unit test based on these examples",
# "button": "Save Example"

"action": "Generate a test specific to this example"
"explanation": "This may help you ensure this example is not predicted with low confidence for a new model",
"button": "Create unit test"

"action": "Generate a test to check if the rate of <br>underconfidence</br> rows is decreasing",
"explanation": "This may help you ensure that the underconfidence rate is at an acceptable level",
"button": "Create unit test"

"action": "Open the debugger session on similar examples",
"explanation": "Debugging similar examples may help you find common patterns",
"button": "Open debugger"
```

## Contribution Right Prediction

Title| Description
-- | --
Description|  Tag features that contribute a lot to the prediction
Requirement| NA
Triggering event | When we switch examples and the first or the first two most contributing shapley’s value are really high compared to the rest
Test description |  Check if the chi 2 / Kolmogorov-Smirnov correlation statistical test between the feature and the prediction has a p-value above α=0.05

```
"push_title": f"{str(feature)}=={str(value)} contributes a lot to the prediction",
```

```
"action": "Open the debugger session on similar examples",
"explanation": "Debugging similar examples may help you find common patterns",
"button": "Open debugger"

"action": "Generate a test to check if this correlation holds with the whole dataset",
"explanation": "Correlations may be spurious, double check if it has a business sense",
"button": "Create test"

"action": "Save slice and continue debugging session",
"explanation": "Saving the slice will enable you to create tests more efficiently",
"button": "Save Slice"
```

## Contribution Wrong Prediction (ON HOLD)

Title| Description
-- | --
Description| Tag features that contribute a lot to the prediction and when the example is incorrect
Requirement| Need ground truth
Triggering event | When we switch examples, the first or the first two most contributing shapley’s value are really high compared to the rest and the example is incorrect
Test description | Check if the performance of an F1-score/RMSE test is more than 10% different between a slice for the corresponding feature value and the whole dataset
```
"push_title": f"{str(feature)}=={str(value)} is responsible for the incorrect prediction",
```

```
"action": "Filter this debugger session with similar examples",
"explanation": "Debugging similar examples may help you find common patterns",
"button": "Open debugger",

 "action": "Generate a performance difference test",
 "explanation": "This may help ensure this spurious pattern is not common to the whole dataset",
 "button": "Create test",

"action": "Save slice and continue debugging session",
"explanation": "Saving the slice will enable you to use it later",
"button": "Save Slice"
```

## Perturbation 

Title| Description
-- | --
Description| Tag features that make the prediction change after a small variation
Requirement| Applicable only to numerical features and textual feature
Triggering event |  When we switch examples and the prediction changes after: 3 MAD (Median absolute deviation) variation or for textual feature, a small variation such as uppercase or punctuation transformation
Test description | Check if the prediction change ratio is not higher than a certain threshold after the perturbation of the whole dataset
```
 Check if the prediction change ratio is not higher than a certain threshold after the perturbation of the whole dataset
```

```
"action": "Generate a robustness test that slightly perturbs this feature",
"explanation": "This will enable you to make sure the model is invariant against similar small changes",
"button": "Create test"
```
