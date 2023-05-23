from giskard.scanner.prediction.prediction_biais import OverconfidenceBiaisDetector,BorderlineBiaisDetector
def test_prediction_biais_detector(german_credit_model, german_credit_data):
    res = OverconfidenceBiaisDetector(metrics=["probamae"]).run(german_credit_model, german_credit_data)
    res2= BorderlineBiaisDetector(metrics=["borderline"]).run(german_credit_model, german_credit_data)
    
    print(res,res2)

# from giskard.scanner.performance.model_bias_detector import ModelBiasDetector
# def test_data_leakage(german_credit_model, german_credit_data):
#     mbd = ModelBiasDetector(metrics=["dataleakage"]).run(german_credit_model, german_credit_data)
#     print(mbd)
