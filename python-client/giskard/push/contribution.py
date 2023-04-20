import numpy as np
from scipy.stats import zscore
from giskard.ml_worker.core.model_explanation import explain


def contribution(model, ds, idrow):  # data_aug_dict
    shap_res = _contribution_push(model, ds, idrow)
    values = ds.df.iloc[idrow]
    training_label = values[ds.target]
    prediction = model.clf.predict(ds.df.iloc[[idrow]])

    if shap_res is not None:
        for el in shap_res:
            # skip for now the following case
            # if ds.column_types[el] == "category" and training_label != prediction and data_aug_dict(el, values):
            #    print(f"Data augmentation recommended for the slice.............{el}",
            #          el, values[el])
            if training_label != prediction:  # use scan feature ?

                res = [{
                    "sentence": "This value is responsible for the incorrect prediction",
                    "action": "Slice",
                    "value": str(values[el]),
                    "key": str(el),
                },
                    {
                    "sentence": "This correlation may apply to the whole dataset",
                    "action": "Test",
                    "value": str(values[el]),
                    "key": str(el),
                    }
                ]

                return res

            else:
                res = [{
                    "sentence": "This feature contributes a lot to the prediction",
                    "action": "Slice",
                    "value": str(values[el]),
                    "key": str(el),
                },
                    {
                    "sentence": "This correlation may apply to the whole dataset",
                    "action": "Test",
                    "value": str(values[el]),
                    "key": str(el),
                    }
                ]

                return res


def _contribution_push(model, ds, idrow):  # done at each step
    feature_shap = _get_shap_values(model, ds, idrow)
    keys = list(feature_shap.keys())
    zscore_array = np.round(zscore(list(feature_shap.values())) * 2) / 2
    # print(zscore_array)
    k1, k2 = keys[-1], keys[-2]
    if zscore_array[-1] >= 2:
        # print(keys[-1],"is an important feature")
        return [k1]
    elif zscore_array[-1] >= 1.5 and zscore_array[-2] >= 1:
        # print(keys[-1] ,"and", keys[-2] ,"are important features")
        return [k1, k2]
    else:
        return None


def _get_shap_values(model, ds, idrow):  # from gRPC
    return explain(model, ds, ds.df.iloc[idrow])["explanations"][model.meta.classification_labels[0]]


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
    return value_counts
