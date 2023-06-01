import numpy as np
import pandas as pd
import torch
import torch.optim as optim
import torch.nn as nn

from torch.utils.data import TensorDataset, DataLoader
from torch.utils.data.dataset import random_split

from giskard.client.giskard_client import GiskardClient
from giskard import PyTorchModel, Dataset

import re
import httpretty

url = "http://giskard-host:12345"
token = "SECRET_TOKEN"
auth = "Bearer SECRET_TOKEN"
content_type = "application/json"
model_name = "uploaded model"
b_content_type = b"application/json"

class ManualLinearRegression(nn.Module):
    def __init__(self):
        super().__init__()
        self.linear = nn.Linear(1, 1)

    def forward(self, x):
        return self.linear(x)

class FeedforwardNeuralNetModel(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim):
        super(FeedforwardNeuralNetModel, self).__init__()
        self.input_dim=input_dim
        # Linear function
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        # Non-linearity
        self.relu = nn.ReLU()
        # Linear function (readout)
        self.fc2 = nn.Linear(hidden_dim, output_dim)

    def forward(self, x):
        # Linear function
        out = self.fc1(x) #torch.transpose(x,0,1)
        # Non-linearity
        out = self.relu(out)
        # Linear function (readout)
        out = self.fc2(out)
        return out

def make_train_step(model, loss_fn, optimizer):
    def train_step(x, y):
        model.train()
        yhat = model(x)
        loss = loss_fn(y, yhat)
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()
        return loss.item()
    return train_step

@httpretty.activate(verbose=True, allow_net_connect=False)
def test_linear_regression_pytorch_dataloader():
    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    np.random.seed(42)
    x = np.random.rand(100, 1)
    true_a, true_b = 1, 2
    y = true_a + true_b*x + 0.1*np.random.randn(100, 1)

    x_tensor = torch.from_numpy(x).float()
    y_tensor = torch.from_numpy(y).float()

    dataset = TensorDataset(x_tensor, y_tensor)

    train_dataset, val_dataset = random_split(dataset, [80, 20])

    train_loader = DataLoader(dataset=train_dataset, batch_size=16)
    val_loader = DataLoader(dataset=val_dataset, batch_size=20)

    # Estimate a and b
    torch.manual_seed(42)

    # model = ManualLinearRegression().to(device) # model = nn.Sequential(nn.Linear(1, 1)).to(device)

    input_dim = 1
    hidden_dim = 10
    output_dim = 1
    model = FeedforwardNeuralNetModel(input_dim, hidden_dim, output_dim)

    loss_fn = nn.MSELoss(reduction='mean')
    optimizer = optim.SGD(model.parameters(), lr=1e-1)
    train_step = make_train_step(model, loss_fn, optimizer)

    n_epochs = 10
    training_losses = []
    validation_losses = []

    for epoch in range(n_epochs):
        batch_losses = []
        for x_batch, y_batch in train_loader:
            x_batch = x_batch.to(device)
            y_batch = y_batch.to(device)
            loss = train_step(x_batch, y_batch)
            batch_losses.append(loss)
        training_loss = np.mean(batch_losses)
        training_losses.append(training_loss)

        with torch.no_grad():
            val_losses = []
            for x_val, y_val in val_loader:
                x_val = x_val.to(device)
                y_val = y_val.to(device)
                model.eval()
                yhat = model(x_val)
                val_loss = loss_fn(y_val, yhat).item()
                val_losses.append(val_loss)
            validation_loss = np.mean(val_losses)
            validation_losses.append(validation_loss)

        print(f"[{epoch+1}] Training loss: {training_loss:.3f}\t Validation loss: {validation_loss:.3f}")

    df = pd.DataFrame({"x": np.squeeze(x), "y": np.squeeze(y)})
    feature_names = ['x']

    my_model = PyTorchModel(name="my_linear_model",
                            clf=model,
                            feature_names=feature_names,
                            model_type="regression")

    # defining the giskard dataset
    my_test_dataset = Dataset(df.head(), name="test dataset", target="label")

    artifact_url_pattern = re.compile(
        "http://giskard-host:12345/api/v2/artifacts/test-project/models/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/.*")
    models_url_pattern = re.compile("http://giskard-host:12345/api/v2/project/test-project/models")

    httpretty.register_uri(httpretty.POST, artifact_url_pattern)
    httpretty.register_uri(httpretty.POST, models_url_pattern)

    client = GiskardClient(url, token)
    model_id = my_model.save(client, 'test-project', my_test_dataset)

    assert re.match("^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", model_id)

    artifact_requests = [i for i in httpretty.latest_requests() if artifact_url_pattern.match(i.url)]
    assert len(artifact_requests) > 0
    for req in artifact_requests:
        assert req.headers.get("Authorization") == auth
        assert int(req.headers.get("Content-Length")) > 0

    artifact_requests = [i for i in httpretty.latest_requests() if models_url_pattern.match(i.url)]
    assert len(artifact_requests) > 0
    for req in artifact_requests:
        assert req.headers.get("Authorization") == auth
        assert int(req.headers.get("Content-Length")) > 0
        assert req.headers.get("Content-Type") == "application/json"