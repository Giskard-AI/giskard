from giskard.scanner.prediction.prediction_issue_detector import PredictionIssueDetector,\
                                                                    OverConfidence,\
                                                                    Borderline


def test_perturbation_classification(enron_model, enron_data):
    oc = OverConfidence(enron_model, enron_data)
    bl = Borderline(enron_model, enron_data)
    oc.run()
    bl.run()
    print("finished")


def test_perturbation_classification_german(german_credit_model, german_credit_data):
    oc = OverConfidence(german_credit_model, german_credit_data)
    bl = Borderline(german_credit_model, german_credit_data)
    oc.run()
    bl.run()
    print("finished")



