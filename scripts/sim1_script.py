

import matplotlib.pyplot as plt

from blockchain_env.multi_block_sim import BiddingGame

def main():
    # Parameters
    lambda_g: float = 1
    lambda_m: float = 10
    alpha: float = 2
    timesteps: int = 24
    num_simulations: int = 10000
    num_universes: int = 1
    nmev_builders: int = 50
    mev_builders: int = 50

    # Simulation
    bidding_game = BiddingGame(lambda_g, 
                                lambda_m, 
                                alpha, 
                                num_simulations, 
                                timesteps,
                                nmev_builders,
                                mev_builders)
    results = [bidding_game.simulate() for universe in range(num_universes)]

    # Extract results
    nmev_probabilities: float = sum([sum(result) for result in results]) / (num_simulations * num_universes)
    mev_probabilities: float = 1 - nmev_probabilities
    print(f"Non-MEV Winner P: {nmev_probabilities} and MEV Winner P: {mev_probabilities}")

    # Plotting
    # Probability plot
    plt.subplot(2, 1, 1)
    labels = ["Probability for Non-MEV Builder", "Probability for MEV Builder"]
    plt.bar(labels, [nmev_probabilities, mev_probabilities])
    plt.ylabel("Probability")

    # Maximum bids over time plot
    plt.subplot(2, 1, 2)
    for i, max_bids in enumerate(bidding_game.max_bids):
        plt.plot(range(1, num_simulations + 1), max_bids, label=f"Universe {i + 1}")

    plt.xlabel("Time Step")
    plt.ylabel("Maximum Bid")
    plt.legend()

    plt.show()

if __name__ == "__main__":
    main()