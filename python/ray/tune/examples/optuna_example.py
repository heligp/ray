"""This test checks that Optuna is functional.

It also checks that it is usable with a separate scheduler.
"""
import time

import ray
from ray import tune
from ray.tune.schedulers import AsyncHyperBandScheduler
from ray.tune.suggest.optuna import OptunaSearch


def evaluation_fn(step, width, height):
    return (0.1 + width * step / 100)**(-1) + height * 0.1


def easy_objective(config):
    # Hyperparameters
    width, height = config["width"], config["height"]

    for step in range(config["steps"]):
        # Iterative training function - can be any arbitrary training procedure
        intermediate_score = evaluation_fn(step, width, height)
        # Feed the score back back to Tune.
        tune.report(iterations=step, mean_loss=intermediate_score)
        time.sleep(0.1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--smoke-test", action="store_true", help="Finish quickly for testing")
    args, _ = parser.parse_known_args()
    ray.init(configure_logging=False)

    tune_kwargs = {
        "num_samples": 10 if args.smoke_test else 100,
        "config": {
            "steps": 100,
            "width": tune.uniform(0, 20),
            "height": tune.uniform(-100, 100),
            # This is an ignored parameter.
            "activation": tune.choice(["relu", "tanh"])
        }
    }
    algo = OptunaSearch(metric="mean_loss", mode="min")
    scheduler = AsyncHyperBandScheduler(metric="mean_loss", mode="min")
    tune.run(
        easy_objective, search_alg=algo, scheduler=scheduler, **tune_kwargs)
