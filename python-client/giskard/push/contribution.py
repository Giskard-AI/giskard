import numpy as np
from scipy.stats import zscore

from giskard.core.core import SupportedModelTypes
from .utils import slice_bounds
from ..models.model_explanation import explain
from ..push import ContributionPush


def contribution(model, ds, idrow):  # data_aug_dict
    if model.meta.model_type == SupportedModelTypes.CLASSIFICATION and _existing_shap_values(ds):
        shap_res = _contribution_push(model, ds, idrow)
        slice_df = ds.slice(lambda df: df.loc[[idrow]], row_level=False)  # Should fix the error
        values = slice_df.df  # It was ds.df.iloc[idrow] before
        training_label = values[ds.target].values
        prediction = model.predict(slice_df).prediction  # Should be fixed
        if shap_res is not None:
            for el in shap_res:
                bounds = slice_bounds(feature=el, value=values[el].values, ds=ds)
                # skip for now the following case
                # if ds.column_types[el] == "category" and training_label != prediction and data_aug_dict(el, values):
                #    print(f"Data augmentation recommended for the slice.............{el}",
                #          el, values[el])
                if training_label != prediction:  # use scan feature ?
                    res = ContributionPush(feature=el,
                                           value=values[el],
                                           bounds=bounds,
                                           model_type=SupportedModelTypes.CLASSIFICATION,
                                           correct_prediction=False
                                           )
                    return res

                else:
                    res = ContributionPush(feature=el,
                                           value=values[el],
                                           bounds=bounds,
                                           model_type=SupportedModelTypes.CLASSIFICATION,
                                           correct_prediction=True
                                           )
                    return res

    if model.meta.model_type == SupportedModelTypes.REGRESSION and _existing_shap_values(ds):
        shap_res = _contribution_push(model, ds, idrow)
        values = ds.df.iloc[idrow]
        # re = ds.__dict__
        y = values[ds.target]
        y_hat = model.model.predict(ds.df.drop(columns=[ds.target]).iloc[[idrow]])
        error = abs(y_hat - y)
        # print(shap_res)
        if shap_res is not None:
            for el in shap_res:
                # print(error, rmse_res)
                bounds = slice_bounds(feature=el, value=values[el], ds=ds)
                if abs(error - y) / y >= 0.2:  # use scan feature ?
                    res = ContributionPush(feature=el,
                                           value=values[el],
                                           bounds=bounds,
                                           model_type=SupportedModelTypes.REGRESSION,
                                           correct_prediction=False
                                           )
                    return res

                else:
                    res = ContributionPush(feature=el,
                                           value=values[el],
                                           bounds=bounds,
                                           model_type=SupportedModelTypes.REGRESSION,
                                           correct_prediction=True
                                           )
                    return res


def _contribution_push(model, ds, idrow):  # done at each step
    feature_shap = _get_shap_values(model, ds, idrow)
    keys = list(feature_shap.keys())
    # normed = [i / sum(list(feature_shap.values())) for i in list(feature_shap.values())]
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


def _existing_shap_values(ds):
    shap_values_exist = ('category' in ds.column_types.values()) or ('numeric' in ds.column_types.values())
    return shap_values_exist
