import numpy as np
from scipy.stats import zscore


def contribution_push(feature_shap):  # done at each step
    keys = list(feature_shap.keys())
    zscore_array = np.round(zscore(list(feature_shap.values())) * 2) / 2
    # print(zscore_array)
    k1, k2 = keys[-1], keys[-2]
    if zscore_array[-1] >= 2:

        # print(keys[-1],"is an important feature")
        return ([keys[-1]])
    elif zscore_array[-1] >= 1.5 and zscore_array[-2] >= 1:
        # print(keys[-1] ,"and", keys[-2] ,"are important features")
        return ([keys[-1], keys[-2]])
    else:
        return (False)


def perturb_and_predict(row, feature, model):  # done at each step
    ref_row = row
    row_perturbed = ref_row.copy()
    row_perturbed[feature] *= 1.2  # self.df[feature].std()
    # print(row_perturbed[feature])
    # Predict probabilities for the perturbed input row using the given model
    ref_prob = model.predict(ref_row)
    probabilities = model.predict(row_perturbed)  # .reshape(1, -1)
    return ref_prob[0] != probabilities[0]


def perturbation(row, column_types):
    for feat, type in column_types.items():
        if type == "numeric" and perturb_and_predict(row, feat):
            print(f"Metamorphic test recommanded for the slice.............{feat}=",
                  feat, row[feat])


def contribution(shap_features, training_label, prediction, column_types, data_aug_dict, values):
    shap_res = contribution_push(shap_features)
    if not shap_res.isnull():
        for el in shap_res:
            if column_types[el] == "category" and training_label != prediction and data_aug_dict(el, values):
                print(f"Data augmentation recommanded for the slice.............{el}",
                      el, values[el])
            elif training_label != prediction:  # use scan feature ?
                print(f"Performance test recommanded for the slice.............{el}",
                      el, values[el])
            else:
                print(f"Target highly correlated with the slice.............{el}",
                      el, values[el])


def bins_count(model, dataframe):  # done at the beggining
    df = dataframe

    columns_to_encode = [key for key in model.column_types.keys() if
                         model.column_types[key] == "category"]
    value_counts = {}
    for column in columns_to_encode:
        nunique = df[column].nunique()
        ratio = len(df) / nunique
        counts = df[column].value_counts().to_dict()
        flag = {value: count < ratio for value, count in counts.items()}
        value_counts[column] = {'value_counts': counts,
                                'nunique': nunique,
                                'ratio': ratio,
                                'flag': flag}
    return (value_counts)
