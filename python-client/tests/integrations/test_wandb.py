import wandb
import pytest

# from giskard import scan

wandb.setup(wandb.Settings(mode="disabled", program=__name__, program_relpath=__name__, disable_code=True))


@pytest.mark.parametrize(
    "dataset_name,model_name",
    [
        ("german_credit_data", "german_credit_model"),
    ],
)
def test_logging_to_wandb(dataset_name, model_name, request):
    giskard_dataset = request.getfixturevalue(dataset_name)
    request.getfixturevalue(model_name)

    giskard_dataset.to_wandb()

    # scan_results = scan(giskard_model, giskard_dataset)
    # scan_results.generate_test_suite()
    # scan_results.
