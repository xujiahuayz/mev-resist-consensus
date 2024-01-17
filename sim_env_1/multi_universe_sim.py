import random

import matplotlib.pyplot as plt
from scipy.stats import pareto


class BiddingGame:
    def __init__(
        self,
        lambda_g: float,
        lambda_m: float,
        alpha: float,
        num_simulations: int,
        timesteps: int,
    ):
        self.lambda_g = lambda_g
        self.lambda_m = lambda_m
        self.alpha = alpha
        self.num_simulations = num_simulations
        self.timesteps = timesteps

    def simulate(self):
        results = []

        for _ in range(self.num_simulations):
            builder1: Builder = Builder(self.lambda_g, 0, pareto.rvs(alpha))
            builder2: Builder = Builder(self.lambda_g, self.lambda_m, pareto.rvs(alpha))

            auction: Auction = Auction(builder1, builder2, self.timesteps)
            results.append(auction.run())

        return results


class Builder:
    def __init__(self, gas_scaling: float, mev_scaling: float, characteristic: float):
        self.gas_scaling = gas_scaling
        self.charateristic = characteristic
        self.mev_scaling = mev_scaling

    def calculate_bid(self, W_t: int):
        self.bid = (
            (self.gas_scaling + self.mev_scaling) * (self.charateristic)
            + self.gas_scaling * W_t
            + self.mev_scaling * W_t
        )

    def update_bid(self, W_t: int):
        # I have added in the assumptuion that W_t for both MEV and Gas will not be independent
        # as if number of transactions in the mempool are high, the gas fee will be more and so
        # will the MEV opportunities. The assumption here is both W_t's are equal
        self.bid += self.gas_scaling * W_t + self.mev_scaling * W_t


class Auction:
    def __init__(self, builder1: Builder, builder2: Builder, timesteps: int):
        self.builder1 = builder1
        self.builder2 = builder2
        self.timesteps = timesteps

    def run(self):
        # This generated Wiener process, the specification of which doesn't change the result of the simulations (the scale does)
        W_t: int = random.randint(-1, 1) / 10

        self.builder1.calculate_bid(W_t)
        self.builder2.calculate_bid(W_t)

        # The proposer can end the auction at any time in the block time
        end_time: int = random.randint(0, timesteps)

        for _ in range(end_time):
            W_t = random.randint(-1, 1) / 10
            self.builder1.update_bid(W_t)
            self.builder2.update_bid(W_t)

        return self.builder1.bid > self.builder2.bid


# Parameters
lambda_g: float = 1
lambda_m: float = 1
alpha: float = 2
timesteps: int = 24
num_simulations: int = 10000

# Simulation
bidding_game = BiddingGame(lambda_g, lambda_m, alpha, num_simulations, timesteps)
results: list[bool] = bidding_game.simulate()

# Extract results
nmev_probabilities: float = sum(results) / num_simulations
mev_probabilities: float = 1 - nmev_probabilities
print(f"Non-MEV Winner P: {nmev_probabilities} and MEV Winner P: {mev_probabilities}")

# Plotting
labels = ["Probability for Non-MEV Builder", "Probability for MEV Builder"]
plt.bar(labels, [nmev_probabilities, mev_probabilities])
plt.ylabel("Probability")
plt.show()
