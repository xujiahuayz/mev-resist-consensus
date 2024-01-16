import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import pareto
import random

class BiddingGame:
    def __init__(self, lambda_g, lambda_m, alpha, num_simulations,timesteps):
        self.lambda_g = lambda_g
        self.lambda_m = lambda_m
        self.alpha = alpha
        self.num_simulations = num_simulations
        self.timesteps = timesteps

    def simulate(self):
        results = []

        for _ in range(self.num_simulations):
            builder1 = Builder(self.lambda_g,0, pareto.rvs(alpha))
            builder2 = Builder(self.lambda_g, self.lambda_m, pareto.rvs(alpha))
            
            auction = Auction(builder1, builder2,self.timesteps)
            results.append(auction.run())
        
        return results
    
class Builder:
    def __init__(self, gas_scaling, mev_scaling, characteristic):
        self.gas_scaling = gas_scaling
        self.charateristic = characteristic
        self.mev_scaling = mev_scaling

    def calculate_bid(self, W_t:int):
        self.bid = (self.gas_scaling + self.mev_scaling) * (self.charateristic) + self.gas_scaling * W_t + self.mev_scaling * W_t
    
    def update_bid(self, W_t:int):
        self.bid += self.gas_scaling * W_t + self.mev_scaling * W_t

class Auction:
    def __init__(self, builder1, builder2,timesteps):
        self.builder1 = builder1
        self.builder2 = builder2
        self.timesteps = timesteps

    def run(self):
        W_t = random.choice([-1,1])/10
        self.builder1.calculate_bid(W_t)
        self.builder2.calculate_bid(W_t)

        for _ in range(self.timesteps):
            W_t = random.choice([-1,1])/10
            self.builder1.update_bid(W_t)
            self.builder2.update_bid(W_t)

        return self.builder1.bid > self.builder2.bid

# Parameters
lambda_g = 1
lambda_m = 1
alpha = 2
timesteps = 24
num_simulations = 10000

# Simulation
bidding_game = BiddingGame(lambda_g, lambda_m, alpha, num_simulations, timesteps)
results = bidding_game.simulate()

# Extract results
nmev_probabilities = sum(results) / num_simulations
mev_probabilities = 1 - nmev_probabilities
print(f'Non-MEV Winner P: {nmev_probabilities} and MEV Winner P: {mev_probabilities}')

# Plotting
labels = ['Probability for Non-MEV Builder', 'Probability for MEV Builder']
plt.bar(labels, [nmev_probabilities, mev_probabilities])
plt.ylabel('Probability')
plt.show()
