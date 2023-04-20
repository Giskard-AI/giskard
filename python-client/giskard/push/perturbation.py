def perturbation(model, ds, idrow):
    for feat, coltype in ds.column_types.items():
        if coltype == "numeric" and _perturb_and_predict(model, ds, idrow, feat):
            res = [
                {
                "sentence": "A small variation (+20%) of this feature makes the prediction change, do you want to "
                            "check if this unrobust behavior generalizes to the whole dataset ?",
                "action": "Test",
                "value": str(ds.df.iloc[idrow][feat]),
                "key": str(feat),
            }
            ]
            return res


def _perturb_and_predict(model, ds, idrow, feature):  # done at each step
    ref_row = ds.df.iloc[[idrow]]
    row_perturbed = ref_row.copy()
    row_perturbed[feature] *= 1.2  # 20% perturbation
    # print(row_perturbed[feature])
    # Predict probabilities for the perturbed input row using the given model
    ref_prob = model.clf.predict(ref_row)
    probabilities = model.clf.predict(row_perturbed)  # .reshape(1, -1)
    return ref_prob[0] != probabilities[0]
