# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring,too-many-instance-attributes, too-many-arguments

import matplotlib.pyplot as plt
import numpy as np

def plot_distribution(total_proposer_balance: list[float], total_builder_balance: list[float],
                      initial_balance: float):
    block_numbers = np.arange(len(total_proposer_balance))  # Create an array of block numbers

    # Calculate the total profit (ignoring initial balances) for each block
    total_profit_proposer = (
        np.array(total_proposer_balance) - len(total_proposer_balance) * [initial_balance]
    )

    total_profit_builder = (
        np.array(total_builder_balance) - len(total_builder_balance) * [initial_balance]
    )

    # Calculate the total profit for each block
    total_profit = total_profit_proposer + total_profit_builder

    # Calculate the percentage of proposer and builder profit for each block
    proposer_percentage = (total_profit_proposer / total_profit) * 100
    builder_percentage = (total_profit_builder / total_profit) * 100

    plt.figure(figsize=(10, 6))
    plt.stackplot(block_numbers, proposer_percentage, builder_percentage,
                  labels=['Proposer Profit', 'Builder Profit'], alpha=0.7)
    plt.plot(block_numbers, np.ones_like(block_numbers) * 100, color='black',
             linestyle='--', label='Total (100%)')
    plt.xlabel('Block Number')
    plt.ylabel('Percentage')
    plt.legend(loc='upper left')
    plt.grid(False)
    plt.title('Percentage Distribution of Proposer and Builder Profits Over Blocks')
    plt.show()
    plt.savefig('./profit_distribution.pdf')

def plot_equilibrium():

    def probability_of_acceptance(bid, t, k, t_avg):
        return min(1, np.exp(-k * bid) * (t / t_avg))

    def expected_payout(bid, t, k, t_avg):
        return probability_of_acceptance(bid, t, k, t_avg) * bid

    def find_equilibrium(t, k, t_avg, bid_range):
        best_bid = 0
        max_payout = 0

        for bid in bid_range:
            payout = expected_payout(bid, t, k, t_avg)
            if payout > max_payout:
                max_payout = payout
                best_bid = bid

        return best_bid, max_payout

    # Constants
    k = 0.1
    t_avg = 50
    ts = [30, 50, 70, 90]

    bid_range = np.linspace(0, 100, 1000)

    # Find the equilibrium
    for t in ts:
        best_bid, max_payout = find_equilibrium(t, k, t_avg, bid_range)
        print(f"Total Fee: {t} - Best Bid: {best_bid}, Max Expected Payout: {max_payout}")

    # # Output the results
    # print("Best Bid:", best_bid)
    # print("Max Expected Payout:", max_payout)

        plt.plot(bid_range, [expected_payout(bid, t, k, t_avg) for bid in bid_range],
                  label=f"T={t}")

    plt.xlabel('Bid')
    plt.ylabel('Expected Payout')
    plt.title('Expected Payout vs. Bid')
    plt.show()

def plot_payoff():
    # Constants
    k = 0.1
    t_avg = 100
    t_values = [50, 100, 150]

    # Bid range
    b = np.linspace(0, 100, 400)

    plt.figure(figsize=(10, 6))

    # Plot for each T value
    for t in t_values:
        p_acceptance = np.minimum(1, np.exp(-k * b) * t / t_avg)
        plt.plot(b, p_acceptance, label=f'T={t}')

    plt.title('Probability of Acceptance vs Bid')
    plt.xlabel('Bid (b)')
    plt.ylabel('Probability of Acceptance')
    plt.legend()
    plt.grid(True)
    plt.show()


def plot_utility():

# Utility function calculation
    def calculate_utility(bid, transaction_fees, mev_profits, kb):
        acceptance_probability = np.minimum(1, np.exp(kb * bid))
        return acceptance_probability * (transaction_fees - bid + mev_profits)

    # Constants and ranges
    kb = -0.1  # Negative as higher bids should decrease the probability
    bids = np.linspace(0, 10, 100)  # Range of bids from 0 to 10
    transaction_fees = 5  # Constant transaction fees
    mev_profits = 2  # Constant MEV profits

    # Calculate utilities for each bid
    utilities = [calculate_utility(bid, transaction_fees, mev_profits, kb) for bid in bids]

    # Plotting
    plt.figure(figsize=(10, 6))
    plt.plot(bids, utilities, label='Builder Utility')
    plt.xlabel('Bid')
    plt.ylabel('Utility')
    plt.title('Builder Utility as a Function of Bid')
    plt.legend()
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    # plot_payoff()
    # plot_equilibrium()

    plot_utility()
