import numpy as np
from scipy.stats import zscore

from giskard.core.core import SupportedModelTypes
from giskard.ml_worker.core.model_explanation import explain
from giskard.ml_worker.testing.tests.performance import test_rmse
from ..push import Push


def contribution(model, ds, idrow):  # data_aug_dict
    if model.meta.model_type == SupportedModelTypes.CLASSIFICATION:
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
                    res = Push(push_type="contribution_wrong", feature=el, value=values[el])
                    yield res

                else:
                    res = Push(push_type="contribution_only", feature=el, value=values[el])
                    yield res

    if model.meta.model_type == SupportedModelTypes.REGRESSION:
        shap_res = _contribution_push(model, ds, idrow)
        values = ds.df.iloc[idrow]
        # re = ds.__dict__
        y = values[ds.target]
        y_hat = model.clf.predict(ds.df.drop(columns=[ds.target]).iloc[[idrow]])
        error = abs(y_hat - y)
        rmse_res = test_rmse(ds, model).execute()
        # print(shap_res)
        if shap_res is not None:
            for el in shap_res:
                # print(error, rmse_res)
                if abs(error - rmse_res.metric) / rmse_res.metric >= 0.2:  # use scan feature ?
                    res = Push(push_type="contribution_wrong",
                               feature=el,
                               value=values[el]
                               )
                    yield res

                else:
                    res = Push(push_type="contribution_only", feature=el, value=values[el])
                    yield res


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
    if model.meta.model_type == SupportedModelTypes.CLASSIFICATION:
        return explain(model, ds, ds.df.iloc[idrow])["explanations"][model.meta.classification_labels[0]]
    elif model.meta.model_type == SupportedModelTypes.REGRESSION:
        return explain(model, ds, ds.df.iloc[idrow])["explanations"]["default"]


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
