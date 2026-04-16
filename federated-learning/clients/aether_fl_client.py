from __future__ import annotations

import os
import flwr as fl
import numpy as np


def get_model_parameters(model):
    return [layer.copy() for layer in model]


def set_model_parameters(model, parameters):
    for i, arr in enumerate(parameters):
        model[i] = arr.copy()


def train(model, trainset, epochs=2):
    """Dummy local training: add tiny noise to simulate gradient updates."""
    history = []
    for epoch in range(epochs):
        for i in range(len(model)):
            model[i] = model[i] + np.random.normal(0, 0.001, size=model[i].shape).astype(np.float32)
        history.append({"loss": float(max(0.01, 1.0 / (epoch + 1)))})
    return history


def evaluate(model, testset):
    """Dummy evaluation."""
    loss = float(np.random.uniform(0.05, 0.25))
    accuracy = float(np.random.uniform(0.75, 0.98))
    return loss, accuracy


def compute_data_quality_score(trainset):
    """Very simple placeholder score.
    Replace with completeness/consistency/drift-aware scoring later.
    """
    size_score = min(1.0, len(trainset) / 1000.0)
    return float(max(0.5, size_score))


class AetherFLClient(fl.client.NumPyClient):
    def __init__(self, model, trainset, testset):
        self.model = model
        self.trainset = trainset
        self.testset = testset

    def get_parameters(self, config):
        return get_model_parameters(self.model)

    def fit(self, parameters, config):
        set_model_parameters(self.model, parameters)
        history = train(self.model, self.trainset, epochs=int(config.get("epochs", 2)))
        quality = compute_data_quality_score(self.trainset)
        return (
            get_model_parameters(self.model),
            len(self.trainset),
            {
                "data_quality_score": float(quality),
                "train_loss": float(history[-1]["loss"]),
            },
        )

    def evaluate(self, parameters, config):
        set_model_parameters(self.model, parameters)
        loss, accuracy = evaluate(self.model, self.testset)
        return float(loss), len(self.testset), {"accuracy": float(accuracy)}


def build_dummy_model():
    return [
        np.zeros((8, 4), dtype=np.float32),
        np.zeros((4,), dtype=np.float32),
        np.zeros((4, 2), dtype=np.float32),
        np.zeros((2,), dtype=np.float32),
    ]


def build_dummy_dataset(size):
    return list(range(size))


def main():
    tenant_name = os.environ.get("AETHER_TENANT_NAME", "tenant-local")
    print(f"Starting client for {tenant_name}")

    model = build_dummy_model()
    trainset = build_dummy_dataset(int(os.environ.get("AETHER_TRAINSET_SIZE", "500")))
    testset = build_dummy_dataset(int(os.environ.get("AETHER_TESTSET_SIZE", "100")))

    client = AetherFLClient(model, trainset, testset)

    fl.client.start_numpy_client(
        server_address="127.0.0.1:8080",
        client=client,
    )


if __name__ == "__main__":
    main()
