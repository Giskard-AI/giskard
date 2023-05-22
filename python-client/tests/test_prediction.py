from giskard.scanner.prediction.prediction_issue_detector import PredictionIssueDetector,\
                                                                    OverConfidence,\
                                                                    Borderline
from giskard.scanner.prediction.metric import OverconfidenceDetector
from giskard.slicing.tree_slicer import DecisionTreeSlicer
from giskard.slicing.category_slicer import CategorySlicer
from giskard.scanner.prediction.prediction_biais import PredictionBiasDetector
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



def test_detector(german_credit_model, german_credit_data):
    oc = OverconfidenceDetector(german_credit_model, german_credit_data)

def test_slicer_on_numerical_feature(german_credit_model, german_credit_data):
    oc = OverconfidenceDetector(german_credit_model, german_credit_data)
    dataset = oc.get_dataset()
    slicer = DecisionTreeSlicer(dataset)
    for key,val in dataset.column_types.items():
        if key != "__gsk__loss" and val=="numeric":
            slices = slicer.find_slices(features=[key], target="__gsk__loss")
            print(slices)

    slicer = CategorySlicer(dataset)
    for key,val in dataset.column_types.items():
        if key != "__gsk__loss" and val=="category":
            slices = slicer.find_slices(features=[key], target="__gsk__loss")
            print(slices)

    # slices = [s for s in slices if 0.05 * len(dataset) <= len(dataset.slice(s))]
    #
    # # Create issues from the slices
    # issues = self._find_issues(slices, model, dataset)

def test_prediction_biais_detector(german_credit_model, german_credit_data):
    PBD = PredictionBiasDetector()
    res = PBD.run(german_credit_model, german_credit_data)
    print(res)

