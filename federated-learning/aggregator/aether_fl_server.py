from __future__ import annotations

import flwr as fl
import numpy as np


class AetherFederatedStrategy(fl.server.strategy.FedAvg):
    """Quality-weighted FedAvg: tenants with higher data quality
    receive proportionally larger weight in gradient aggregation.
    Quality is computed locally and sent only as a scalar score.
    Raw data never leaves the tenant boundary.
    """

    def aggregate_fit(self, server_round, results, failures):
        if not results:
            return None, {}

        weighted = [
            (
                fl.common.parameters_to_ndarrays(fit_res.parameters),
                float(fit_res.metrics.get("data_quality_score", 1.0)),
                int(fit_res.num_examples),
            )
            for _, fit_res in results
        ]

        total_weight = sum(q * n for _, q, n in weighted)
        if total_weight <= 0:
            total_weight = 1.0

        aggregated = [
            np.sum(
                [params[i] * (q * n / total_weight) for params, q, n in weighted],
                axis=0,
            )
            for i in range(len(weighted[0][0]))
        ]

        avg_quality = sum(q for _, q, _ in weighted) / len(weighted)
        print(
            f"Round {server_round}: {len(results)} clients, "
            f"avg quality {avg_quality:.3f}"
        )

        metrics = {
            "avg_data_quality_score": float(avg_quality),
            "num_clients": int(len(results)),
        }

        return fl.common.ndarrays_to_parameters(aggregated), metrics


def build_initial_parameters():
    """Small dummy 2-layer linear model weights as NumPy arrays.
    Replace with your real model initialization later.
    """
    weights = [
        np.zeros((8, 4), dtype=np.float32),
        np.zeros((4,), dtype=np.float32),
        np.zeros((4, 2), dtype=np.float32),
        np.zeros((2,), dtype=np.float32),
    ]
    return fl.common.ndarrays_to_parameters(weights)


def main():
    strategy = AetherFederatedStrategy(
        fraction_fit=1.0,
        fraction_evaluate=1.0,
        min_fit_clients=3,
        min_evaluate_clients=3,
        min_available_clients=3,
        initial_parameters=build_initial_parameters(),
    )

    # Flower server bootstrap
    fl.server.start_server(
        server_address="0.0.0.0:8080",
        config=fl.server.ServerConfig(num_rounds=3),
        strategy=strategy,
    )


if __name__ == "__main__":
    main()
