

import matplotlib.pyplot as plt

from blockchain_env.multi_block_sim import BiddingGame

def main():
    # Parameters
    lambda_g: float = 1
    lambda_m: float = 1
    alpha: float = 2
    timesteps: int = 24
    num_simulations: int = 100
    num_universes: int = 10

    # Simulation
    bidding_game = BiddingGame(lambda_g, 
                                lambda_m, 
                                alpha, 
                                num_simulations, 
                                timesteps,
                                50,
                                50)
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